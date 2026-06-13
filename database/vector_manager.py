
import chromadb
import os
import re
import logging
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma

from langchain_classic.retrievers.self_query.base import SelfQueryRetriever
from langchain_classic.chains.query_constructor.base import AttributeInfo

# 텍스트 분할을 위한 import (의미적 청킹 대안)
from langchain_text_splitters import RecursiveCharacterTextSplitter
import numpy as np

from config import config

logger = logging.getLogger(__name__)

class VectorDBManager:
    _instance = None
    _initialized = False

    COLLECTION_NAMES = {
        'chunks': 'meeting_chunks',
        'subtopic': 'meeting_subtopic',
    }

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, persist_directory="./database/vector_db", upload_folder="./uploads", db_manager=None):
        if self._initialized:
            return
        if not config.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY가 .env 파일에 설정되지 않았습니다.")

        self.client = chromadb.PersistentClient(path=persist_directory)
        self.embedding_function = OpenAIEmbeddings(model=config.EMBEDDING_MODEL)
        self.upload_folder = upload_folder

        # DatabaseManager 인스턴스 (외부에서 주입받음, SQLite 삭제를 위해)
        self.db_manager = db_manager

        # Initialize LLM for SelfQueryRetriever
        self.llm = ChatOpenAI(api_key=config.OPENAI_API_KEY, temperature=0)

        self.vectorstores = {
            key: Chroma(
                client=self.client,
                collection_name=name,
                embedding_function=self.embedding_function,
            )
            for key, name in self.COLLECTION_NAMES.items()
        }

        # Define metadata field information for SelfQueryRetriever
        self.metadata_field_infos = {
            "chunks": [
                AttributeInfo(name="dialogue_id", description="The unique identifier for the dialogue within the meeting", type="string"),
                AttributeInfo(name="chunk_index", description="The index of the chunk within the meeting", type="integer"),
                AttributeInfo(
                    name="title",
                    description="회의 제목 또는 노트 이름. 사용자 쿼리에서 회의/노트 이름이 언급되면 이 필드로 필터링. 부분 일치 검색 가능. 예: 쿼리에 '사자회담'이 있으면 title에 '사자회담'이 포함된 모든 문서",
                    type="string"
                ),
                AttributeInfo(
                    name="meeting_date",
                    description="회의 시점을 나타내는 텍스트 필드 (예: '2025-11-07'). 문자열로 저장되며 정확한 일치 검색에 사용됩니다",
                    type="string"
                ),
                AttributeInfo(name="audio_file", description="The name of the audio file for the meeting", type="string"),
                AttributeInfo(name="start_time", description="The start time of the chunk in seconds", type="float"),
                AttributeInfo(name="end_time", description="The end time of the chunk in seconds", type="float"),
                AttributeInfo(name="speaker_count", description="The number of different speakers in the chunk", type="integer"),
            ],
            "subtopic": [
                AttributeInfo(
                    name="meeting_title",
                    description="회의 제목 또는 노트 이름. 사용자 쿼리에서 회의/노트 이름이 언급되면 이 필드로 필터링. 부분 일치 검색 가능. 예: 쿼리에 '사자회담'이 있으면 meeting_title에 '사자회담'이 포함된 모든 문서",
                    type="string"
                ),
                AttributeInfo(
                    name="meeting_date",
                    description="회의 시점을 나타내는 텍스트 필드 (예: '2025-11-07'). 문자열로 저장되며 정확한 일치 검색에 사용됩니다",
                    type="string"
                ),
                AttributeInfo(name="audio_file", description="The name of the audio file for the meeting", type="string"),
                AttributeInfo(name="main_topic", description="The main topic of the summarized sub-chunk", type="string"),
                AttributeInfo(name="summary_index", description="The index of the summary sub-chunk", type="integer"),
            ],
        }

        # Define document content descriptions for SelfQueryRetriever
        self.document_content_descriptions = {
            "chunks": "회의 대화 내용의 의미론적으로 그룹화된 청크 (화자 라벨 및 타임스탬프 포함)",
            "subtopic": "회의록의 요약된 하위 주제",
        }

        logger.info(f"✅ VectorDBManager for collections {list(self.COLLECTION_NAMES.values())} initialized.")

        self._initialized = True

    def _clean_text(self, formatted_text: str) -> str:
        """
        정규표현식을 사용해서 [Speaker X, MM:SS] 형식의 정보를 제거합니다.

        Args:
            formatted_text (str): [Speaker X, MM:SS] 형식이 포함된 텍스트

        Returns:
            str: 순수한 대화 텍스트 (speaker와 시간 정보 제거)
        """
        # [Speaker X, MM:SS] 패턴 제거
        # [^,]+ : 쉼표가 아닌 문자 (숫자, "Unknown" 등)
        # \d{2}:\d{2} : MM:SS 형식
        pattern = r'\[Speaker [^,]+, \d{2}:\d{2}\]\s*'
        cleaned_text = re.sub(pattern, '', formatted_text)

        # 빈 줄 제거
        cleaned_text = '\n'.join(line for line in cleaned_text.split('\n') if line.strip())

        return cleaned_text.strip()

    def add_meeting_as_chunk(self, meeting_id, title, meeting_date, audio_file, segments):
        """
        회의 대화 내용을 스마트하게 청크로 묶어 DB에 저장합니다.
        화자 변경, 시간 간격을 고려하여 청킹하며, Gemini를 사용해서 speaker와 시간 정보를 제거합니다.

        Args:
            meeting_id (str): 회의 ID
            title (str): 회의 제목
            meeting_date (str): 회의 일시
            audio_file (str): 오디오 파일명
            segments (list): 회의 대화 세그먼트 리스트
                각 세그먼트는 {'speaker_label', 'start_time', 'segment', ...} 포함
        """
        chunk_vdb = self.vectorstores['chunks']

        try:
            # 1. 스마트 청킹: 화자 변경과 시간 간격을 고려
            chunks = self._create_smart_chunks(segments, max_chunk_size=1000, time_gap_threshold=60)

            logger.info(f"📦 스마트 청킹으로 {len(chunks)}개의 청크 생성 완료")

            # 2. 정규표현식으로 각 청크의 텍스트 정제 (speaker와 시간 정보 제거)
            logger.info(f"🔧 정규표현식으로 텍스트 정제 중...")
            for chunk in chunks:
                chunk['text'] = self._clean_text(chunk['text'])

            # 3. 각 청크를 Vector DB에 저장
            chunk_texts = []
            chunk_metadatas = []
            chunk_ids = []

            for i, chunk_info in enumerate(chunks):
                chunk_texts.append(chunk_info['text'])
                # meeting_date를 문자열로 강제 변환 (datetime 객체일 경우 대비)
                meeting_date_str = str(meeting_date) if meeting_date else ""
                chunk_metadatas.append({
                    "meeting_id": meeting_id,
                    "dialogue_id": f"{meeting_id}_chunk_{i}",
                    "chunk_index": i,
                    "title": title,
                    "meeting_date": meeting_date_str,
                    "audio_file": audio_file,
                    "start_time": chunk_info['start_time'],
                    "end_time": chunk_info['end_time'],
                    "speaker_count": chunk_info['speaker_count']
                })
                chunk_ids.append(f"{meeting_id}_chunk_{i}")

            # Vector DB에 추가
            chunk_vdb.add_texts(
                texts=chunk_texts,
                metadatas=chunk_metadatas,
                ids=chunk_ids
            )

            logger.info(f"✅ {len(chunks)}개의 스마트 청크를 meeting_chunks DB에 저장 완료 (meeting_id: {meeting_id})")

        except Exception as e:
            logger.warning(f"⚠️ 스마트 청킹 중 오류 발생: {e}")
            logger.info(f"📝 대신 기본 청킹 방식을 사용합니다.")

            # 에러 발생 시 폴백: RecursiveCharacterTextSplitter 사용
            formatted_segments = []
            for seg in segments:
                speaker = seg.get('speaker_label', 'Unknown')
                start_time = seg.get('start_time', 0)
                text = seg.get('segment', '')
                minutes = int(start_time // 60)
                seconds = int(start_time % 60)
                time_str = f"{minutes:02d}:{seconds:02d}"
                formatted_text = f"[Speaker {speaker}, {time_str}] {text}"
                formatted_segments.append(formatted_text)

            full_text = "\n".join(formatted_segments)

            # RecursiveCharacterTextSplitter로 청킹
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                separators=["\n[Speaker", "\n\n", "\n", " ", ""]
            )

            split_chunks = text_splitter.split_text(full_text)

            # 정규표현식으로 텍스트 정제
            logger.info(f"🔧 정규표현식으로 폴백 텍스트 정제 중...")
            cleaned_chunks = [self._clean_text(chunk) for chunk in split_chunks]

            chunk_texts = []
            chunk_metadatas = []
            chunk_ids = []

            for i, chunk_text in enumerate(cleaned_chunks):
                chunk_texts.append(chunk_text)
                # meeting_date를 문자열로 강제 변환 (datetime 객체일 경우 대비)
                meeting_date_str = str(meeting_date) if meeting_date else ""
                chunk_metadatas.append({
                    "meeting_id": meeting_id,
                    "dialogue_id": f"{meeting_id}_chunk_{i}",
                    "chunk_index": i,
                    "title": title,
                    "meeting_date": meeting_date_str,
                    "audio_file": audio_file
                })
                chunk_ids.append(f"{meeting_id}_chunk_{i}")

            chunk_vdb.add_texts(
                texts=chunk_texts,
                metadatas=chunk_metadatas,
                ids=chunk_ids
            )

            logger.info(f"✅ {len(split_chunks)}개의 청크를 meeting_chunks DB에 저장 완료 (폴백 모드)")

    def _create_smart_chunks(self, segments, max_chunk_size=1000, time_gap_threshold=60):
        """
        화자 변경, 시간 간격을 고려한 스마트 청킹

        Args:
            segments (list): 회의 대화 세그먼트 리스트
            max_chunk_size (int): 최대 청크 크기 (문자 수)
            time_gap_threshold (int): 시간 간격 임계값 (초)

        Returns:
            list: 청크 정보 리스트 [{'text': str, 'start_time': float, 'end_time': float, 'speaker_count': int}]
        """
        chunks = []
        current_chunk = []
        current_chunk_text = ""
        current_speaker = None
        last_time = 0
        speakers_in_chunk = set()

        for seg in segments:
            speaker = seg.get('speaker_label', 'Unknown')
            start_time = seg.get('start_time', 0)
            text = seg.get('segment', '')

            # 시간을 MM:SS 형식으로 변환
            minutes = int(start_time // 60)
            seconds = int(start_time % 60)
            time_str = f"{minutes:02d}:{seconds:02d}"

            # 포맷팅된 텍스트
            formatted_text = f"[Speaker {speaker}, {time_str}] {text}"

            # 청크 분리 조건:
            # 1. 현재 청크 크기가 max_chunk_size를 초과
            # 2. 시간 간격이 time_gap_threshold 초과 (긴 침묵이나 주제 전환 가능성)
            # 3. 화자가 변경되고 현재 청크가 충분히 큼 (500자 이상)

            time_gap = start_time - last_time
            should_split = False

            if len(current_chunk_text) + len(formatted_text) > max_chunk_size:
                should_split = True
            elif time_gap > time_gap_threshold and len(current_chunk_text) > 200:
                should_split = True
            elif speaker != current_speaker and len(current_chunk_text) > 500:
                # 화자 변경 시 적당한 크기면 분리
                should_split = True

            if should_split and current_chunk:
                # 현재 청크 저장
                chunks.append({
                    'text': current_chunk_text.strip(),
                    'start_time': current_chunk[0].get('start_time', 0),
                    'end_time': current_chunk[-1].get('start_time', 0),
                    'speaker_count': len(speakers_in_chunk)
                })

                # 새 청크 시작
                current_chunk = []
                current_chunk_text = ""
                speakers_in_chunk = set()

            # 현재 청크에 추가
            current_chunk.append(seg)
            current_chunk_text += formatted_text + "\n"
            speakers_in_chunk.add(speaker)
            current_speaker = speaker
            last_time = start_time

        # 마지막 청크 저장
        if current_chunk:
            chunks.append({
                'text': current_chunk_text.strip(),
                'start_time': current_chunk[0].get('start_time', 0),
                'end_time': current_chunk[-1].get('start_time', 0),
                'speaker_count': len(speakers_in_chunk)
            })

        return chunks


    def add_meeting_as_subtopic(self, meeting_id, title, meeting_date, audio_file, summary_content):
        """스크립트 전체를 소주제별 청크로 DB에 저장합니다."""

        
        # 1. 생성된 요약을 주제별로 파싱
        # "### "로 분리하되, 첫 번째 요소가 공백일 경우를 대비해 filter(None, ...) 사용
        summary_chunks = summary_content.split('\n### ')
        summary_chunks = [chunk.strip() for chunk in summary_chunks if chunk.strip()]
        
        # 첫 번째 청크에 "### "가 누락되었을 수 있으므로, 첫 번째 청크만 따로 처리
        # if summary_chunks and not summary_chunks[0].startswith('###'):
        #      # 첫번째 청크가 ###로 시작하지 않으면 ###를 붙여준다.
        #      if summary_chunks[0].count('\n') > 0:
        #          summary_chunks[0] = '### ' + summary_chunks[0]

        logger.info("===============summary_chunks=================")
        logger.info(summary_chunks)
        
        # 2. 각 요약 chunk를 Summary_Analysis_DB에 저장
        subtopic_vdb = self.vectorstores['subtopic']
        chunk_texts = []
        chunk_metadatas = []
        chunk_ids = []

        for i, chunk in enumerate(summary_chunks):
            # '### '가 없는 경우를 대비하여, 첫 줄을 main_topic으로 추출
            lines = chunk.split('\n')
            main_topic = lines[0].replace('### ', '').strip()

            # 실제 저장될 내용은 '### '를 포함한 전체 청크
            full_chunk_content = '### ' + chunk if not chunk.startswith('###') else chunk

            # meeting_date를 문자열로 강제 변환 (datetime 객체일 경우 대비)
            meeting_date_str = str(meeting_date) if meeting_date else ""

            chunk_texts.append(full_chunk_content)
            chunk_metadatas.append({
                "meeting_id": meeting_id,
                "meeting_title": title,
                "meeting_date": meeting_date_str,
                "audio_file": audio_file,
                "main_topic": main_topic,
                "summary_index": i
            })
            chunk_ids.append(f"{meeting_id}_summary_{i}")

        if chunk_texts:
            subtopic_vdb.add_texts(texts=chunk_texts, metadatas=chunk_metadatas, ids=chunk_ids)
            logger.info(f"📄 요약 결과 {len(chunk_texts)}개를 Summary_Analysis_DB에 저장했습니다.")
            return summary_chunks
        else:
            logger.warning("⚠️ 요약 결과에서 유효한 청크를 찾지 못했습니다.")



    
    
    def search(self,
             db_type: str,
             query: str,
             k: int = 5,
             retriever_type: str = "similarity",
             filter_criteria: dict = None,
             score_threshold: float = None,  # <-- [수정됨] 점수 임계값 추가
             mmr_fetch_k: int = 20,         # <-- [수정됨] MMR fetch_k 추가
             mmr_lambda_mult: float = 0.5   # <-- [수정됨] MMR lambda_mult 추가
             ) -> list:
        """
        지정된 DB에서 쿼리와 필터 조건을 사용하여 문서를 검색합니다.
        score_threshold가 지정되면 retriever_type은 'similarity_score_threshold'로 자동 변경됩니다.

        Args:
            db_type (str): 검색할 DB 타입 ('chunks', 'subtopic').
            query (str): 검색할 텍스트 쿼리.
            k (int, optional): 반환할 결과의 수. Defaults to 5.
            retriever_type (str, optional): 사용할 리트리버 타입 ('similarity', 'mmr', 'self_query', 'similarity_score_threshold'). Defaults to "similarity".
            filter_criteria (dict, optional): 메타데이터 필터링 조건 (예: {'meeting_id': '...', 'audio_file': '...'}). Defaults to None.
            score_threshold (float, optional): 유사도 점수 임계값 (0.0~1.0). Defaults to None.
            mmr_fetch_k (int, optional): MMR에서 초기 fetch할 문서 수. Defaults to 20.
            mmr_lambda_mult (float, optional): MMR의 다양성 파라미터 (0.0~1.0). Defaults to 0.5.

        Returns:
            list: LangChain Document 객체 리스트.
        """
        # 1. Validate inputs
        if db_type not in self.vectorstores:
            raise ValueError(f"Unknown db_type: {db_type}. Available types are {list(self.vectorstores.keys())}")

        # [수정됨] "similarity_score_threshold"를 유효한 타입으로 허용
        allowed_types = ["similarity", "mmr", "self_query", "similarity_score_threshold"]
        if retriever_type not in allowed_types:
            raise ValueError(f"Unsupported retriever_type: {retriever_type}. Choose from {allowed_types}.")

        # [수정됨] score_threshold가 제공되면, retriever_type을 강제로 변경
        current_retriever_type = retriever_type
        if score_threshold is not None and retriever_type == "similarity":
            current_retriever_type = "similarity_score_threshold"
            logger.info(f"ℹ️ score_threshold provided. Changing retriever_type to 'similarity_score_threshold'.")

        vdb = self.vectorstores[db_type]
        results = []

        # 2. Handle 'similarity', 'mmr', 'similarity_score_threshold' retrievers
        if current_retriever_type in ["similarity", "mmr", "similarity_score_threshold"]:
            search_kwargs = {'k': k}
            if filter_criteria:
                search_kwargs['filter'] = filter_criteria

            # [수정됨] 타입에 따라 search_kwargs 동적 구성
            if current_retriever_type == "similarity_score_threshold":
                if score_threshold is None:
                    raise ValueError("score_threshold must be provided when retriever_type is 'similarity_score_threshold'")
                search_kwargs['score_threshold'] = score_threshold

            elif current_retriever_type == "mmr":
                search_kwargs['fetch_k'] = mmr_fetch_k
                search_kwargs['lambda_mult'] = mmr_lambda_mult

            retriever = vdb.as_retriever(
                search_type=current_retriever_type,
                search_kwargs=search_kwargs
            )
            results = retriever.invoke(query)

        # 3. Handle 'self_query' retriever
        elif current_retriever_type == "self_query":
            # (참고: SelfQueryRetriever는 기본적으로 내부에서 similarity_search를 사용합니다.)
            # (여기서 점수 기반 필터링을 하려면, SelfQueryRetriever를 커스텀해야 할 수도 있습니다.)
            metadata_info = self.metadata_field_infos[db_type]
            doc_description = self.document_content_descriptions[db_type]

            try:
                retriever = SelfQueryRetriever.from_llm(
                    self.llm,
                    vdb,
                    doc_description,
                    metadata_info,
                    verbose=True,
                    base_filter=filter_criteria,
                    # [개선 아이디어] SelfQueryRetriever가 반환할 k의 개수를 설정할 수 있습니다.
                    # 다만, invoke 시점이 아닌 생성 시점에 search_kwargs를 넘겨야 할 수 있습니다. (LangChain 버전에 따라 다름)
                    # enable_limit=True를 사용하고 쿼리에 "top 3 results" 등을 포함시켜야 할 수도 있습니다.
                )
                results = retriever.invoke(query)

                # [수정됨] SelfQuery 이후에도 k개만 반환하도록 강제 (필요시)
                # SelfQueryRetriever는 k를 LLM이 추론하게 하므로, k가 무시될 수 있습니다.
                # 만약 결과가 너무 많다면, k만큼 잘라냅니다.
                if len(results) > k:
                     logger.info(f"ℹ️ SelfQuery found {len(results)} results. Truncating to k={k}.")
                     results = results[:k]

            except Exception as e:
                # SelfQuery 실패 시 similarity search로 폴백
                error_msg = str(e)
                logger.warning(f"⚠️ SelfQuery 실패 (폴백: similarity search): {error_msg}")

                # ChromaDB 호환되지 않는 필터 오류인 경우, similarity search로 대체
                if "Expected where operand value" in error_msg or "type" in error_msg:
                    logger.warning("   → ChromaDB 호환되지 않는 필터 형식 감지. similarity search로 전환합니다.")

                search_kwargs = {'k': k}
                if filter_criteria:
                    search_kwargs['filter'] = filter_criteria

                retriever = vdb.as_retriever(
                    search_type="similarity",
                    search_kwargs=search_kwargs
                )
                results = retriever.invoke(query)

        logger.info(f"✅ Found {len(results)} documents from '{self.COLLECTION_NAMES[db_type]}' for query: '{query}'")
        return results

    
    def get_chunks_by_meeting_id(self, meeting_id: str) -> str:
        """
        meeting_id로 청킹된 문서를 chunk_index 순서대로 가져와서 하나의 문자열로 결합합니다.

        Args:
            meeting_id (str): 회의 ID

        Returns:
            str: chunk_index 순서대로 결합된 전체 청크 텍스트
                 (청크가 없으면 빈 문자열 반환)
        """
        try:
            # meeting_chunks 컬렉션에서 해당 meeting_id의 모든 청크 조회
            collection = self.client.get_collection(name=self.COLLECTION_NAMES['chunks'])

            # meeting_id로 필터링하여 모든 항목 가져오기
            results = collection.get(
                where={"meeting_id": meeting_id},
                include=["documents", "metadatas"]
            )

            if not results or not results.get('documents'):
                logger.warning(f"⚠️ meeting_id '{meeting_id}'에 대한 청크를 찾을 수 없습니다.")
                return ""

            # documents와 metadatas를 chunk_index 순서로 정렬
            documents = results['documents']
            metadatas = results['metadatas']

            # (chunk_index, document) 튜플 리스트 생성 후 정렬
            indexed_docs = []
            for doc, meta in zip(documents, metadatas):
                chunk_index = meta.get('chunk_index', 0)
                indexed_docs.append((chunk_index, doc))

            # chunk_index 기준으로 정렬
            indexed_docs.sort(key=lambda x: x[0])

            # 문서들을 순서대로 결합 (각 문서 사이에 줄바꿈 2개 추가)
            full_chunks = "\n\n".join([doc for _, doc in indexed_docs])

            logger.info(f"✅ meeting_id '{meeting_id}'에 대한 {len(indexed_docs)}개의 청크를 순서대로 가져왔습니다.")
            return full_chunks

        except Exception as e:
            logger.error(f"❌ 청크 조회 중 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            return ""

    def get_summary_by_meeting_id(self, meeting_id: str) -> str:
        """
        meeting_id로 문단 요약을 summary_index 순서대로 가져와서 하나의 문자열로 결합합니다.

        Args:
            meeting_id (str): 회의 ID

        Returns:
            str: summary_index 순서대로 결합된 전체 문단 요약 텍스트
                 (요약이 없으면 빈 문자열 반환)
        """
        try:
            # meeting_subtopic 컬렉션에서 해당 meeting_id의 모든 청크 조회
            collection = self.client.get_collection(name=self.COLLECTION_NAMES['subtopic'])

            # meeting_id로 필터링하여 모든 항목 가져오기
            results = collection.get(
                where={"meeting_id": meeting_id},
                include=["documents", "metadatas"]
            )

            if not results or not results.get('documents'):
                logger.warning(f"⚠️ meeting_id '{meeting_id}'에 대한 문단 요약을 찾을 수 없습니다.")
                return ""

            # documents와 metadatas를 summary_index 순서로 정렬
            documents = results['documents']
            metadatas = results['metadatas']

            # (summary_index, document) 튜플 리스트 생성 후 정렬
            indexed_docs = []
            for doc, meta in zip(documents, metadatas):
                summary_index = meta.get('summary_index', 0)
                indexed_docs.append((summary_index, doc))

            # summary_index 기준으로 정렬
            indexed_docs.sort(key=lambda x: x[0])

            # 문서들을 순서대로 결합 (각 문서 사이에 줄바꿈 2개 추가)
            full_summary = "\n\n".join([doc for _, doc in indexed_docs])

            logger.info(f"✅ meeting_id '{meeting_id}'에 대한 {len(indexed_docs)}개의 문단 요약을 순서대로 가져왔습니다.")
            return full_summary

        except Exception as e:
            logger.error(f"❌ 문단 요약 조회 중 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            return ""

    def delete_from_collection(self, db_type, meeting_id=None, audio_file=None, title=None):
        """
        지정된 벡터 DB 컬렉션에서 항목을 삭제합니다.
        db_type이 "all"이면 SQLite, Vector DB (chunks + subtopic), 오디오 파일을 모두 삭제합니다.
        meeting_id, audio_file, title 중 하나 이상이 제공되면 해당 조건에 맞는 항목을 삭제합니다.
        아무것도 제공되지 않으면 해당 db_type의 전체 컬렉션을 삭제합니다.
        """
        # db_type이 "all"이면 모든 데이터 삭제 (SQLite + Vector DB + 오디오 파일)
        if db_type == "all":
            if not meeting_id:
                raise ValueError("meeting_id is required when db_type is 'all'")
            return self._delete_all_meeting_data(meeting_id)

        # 기존 로직: 특정 컬렉션만 삭제
        if db_type not in self.vectorstores:
            raise ValueError(f"Unknown db_type: {db_type}. Must be one of {list(self.COLLECTION_NAMES.keys())}")

        collection = self.client.get_or_create_collection(name=self.COLLECTION_NAMES[db_type])

        filters = {}
        if meeting_id:
            filters["meeting_id"] = meeting_id
        if audio_file:
            filters["audio_file"] = audio_file
        if title:
            filters["title"] = title

        if filters:
            # 특정 필터가 있는 경우
            logger.info(f"🗑️ Deleting from '{db_type}' collection with filters: {filters}")
            collection.delete(where=filters)
            logger.info(f"✅ Deletion from '{db_type}' collection complete.")
        else:
            # 필터가 없는 경우, 전체 컬렉션 삭제
            logger.warning(f"⚠️ No specific filters provided. Deleting ALL items from '{db_type}' collection.")
            collection.delete(where={}) # deletes all items
            logger.info(f"✅ All items deleted from '{db_type}' collection.")

    def _get_audio_file_from_vector_db(self, meeting_id):
        """
        Vector DB에서 meeting_id로 audio_file을 조회합니다.
        SQLite에서 조회 실패 시 폴백으로 사용됩니다.

        Args:
            meeting_id (str): 회의 ID

        Returns:
            str or None: audio_file 이름 또는 None
        """
        try:
            import sqlite3
            conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'database', 'vector_db', 'chroma.sqlite3'))
            cursor = conn.cursor()

            cursor.execute('''
                SELECT string_value
                FROM embedding_metadata
                WHERE key = "audio_file" AND id IN (
                    SELECT DISTINCT id FROM embedding_metadata
                    WHERE key = "meeting_id" AND string_value = ?
                )
                LIMIT 1
            ''', (meeting_id,))

            result = cursor.fetchone()
            conn.close()

            return result[0] if result else None
        except Exception as e:
            logger.warning(f"⚠️ Vector DB에서 audio_file 조회 실패: {e}")
            return None

    def _delete_all_meeting_data(self, meeting_id):
        """
        meeting_id로 모든 회의 데이터를 삭제합니다.
        - SQLite DB: meeting_dialogues, meeting_minutes
        - Vector DB: meeting_chunks, meeting_subtopic
        - 오디오 파일

        Args:
            meeting_id (str): 삭제할 회의 ID

        Returns:
            dict: 삭제 결과 정보
        """
        # db_manager가 주입되지 않은 경우 에러 발생
        if not self.db_manager:
            raise ValueError("DatabaseManager instance is required for deleting all meeting data. Please set db_manager in VectorDBManager constructor.")

        # 삭제 프로세스 시작 로그
        logger.info("\n\n" + "=" * 70)
        logger.info(f"🗑️  [회의 데이터 삭제 프로세스 시작]")
        logger.info("=" * 70)
        logger.info(f"🔑 삭제 키값(meeting_id): {meeting_id}")
        logger.info(f"📍 이 키값을 기준으로 다음 데이터를 검색하여 삭제합니다:")
        logger.info(f"   • SQLite DB - meeting_dialogues 테이블 (WHERE meeting_id = '{meeting_id}')")
        logger.info(f"   • SQLite DB - meeting_minutes 테이블 (WHERE meeting_id = '{meeting_id}')")
        logger.info(f"   • Vector DB - meeting_chunk 컬렉션 (WHERE meeting_id = '{meeting_id}')")
        logger.info(f"   • Vector DB - meeting_subtopic 컬렉션 (WHERE meeting_id = '{meeting_id}')")
        logger.info(f"   • 미디어 파일 (오디오/비디오, uploads 폴더)")
        logger.info("=" * 70)

        # 1. meeting_id로 오디오 파일명 조회 (SQLite 우선, 실패 시 Vector DB)
        audio_file = self.db_manager.get_audio_file_by_meeting_id(meeting_id)

        if not audio_file:
            logger.warning("⚠️ SQLite에서 audio_file을 찾을 수 없습니다. Vector DB에서 조회 시도...")
            audio_file = self._get_audio_file_from_vector_db(meeting_id)

        if not audio_file:
            logger.warning("⚠️ audio_file을 찾을 수 없습니다. 파일 삭제를 건너뜁니다.")
            logger.warning("   (SQLite와 Vector DB 삭제는 계속 진행됩니다)")
            audio_file = None  # 파일 삭제 단계에서 처리
        else:
            logger.info(f"📄 미디어 파일명: {audio_file}")

        logger.info("=" * 70)

        # 2. SQLite DB 삭제
        deleted_sqlite = self.db_manager.delete_meeting_by_id(meeting_id)

        # 3. Vector DB chunks 삭제
        deleted_chunks_count = 0
        before_chunks_count = 0
        after_chunks_count = 0
        try:
            logger.info(f"\n📊 [Vector DB Chunks 삭제 검증 시작] meeting_id = {meeting_id}")
            logger.info("=" * 70)

            # LangChain vectorstore의 underlying collection 사용
            chunks_collection = self.vectorstores['chunks']._collection

            # 삭제 전 전체 데이터 개수 확인 (limit 없이 조회)
            before_delete = chunks_collection.get(where={"meeting_id": meeting_id})
            if before_delete and before_delete.get('ids'):
                before_chunks_count = len(before_delete['ids'])
                logger.info(f"[삭제 전] meeting_chunk: {before_chunks_count}개")
                logger.info("-" * 70)

                # 삭제 실행
                chunks_collection.delete(where={"meeting_id": meeting_id})
                logger.info(f"[삭제 수행] meeting_chunk: {before_chunks_count}개 삭제 시도")
                deleted_chunks_count = before_chunks_count

                logger.info("-" * 70)

                # 삭제 후 확인
                after_delete = chunks_collection.get(where={"meeting_id": meeting_id})
                if after_delete and after_delete.get('ids'):
                    after_chunks_count = len(after_delete['ids'])
                    logger.info(f"[삭제 후] meeting_chunk: {after_chunks_count}개 남음")
                    logger.warning(f"⚠️ Vector DB (meeting_chunk) 삭제 검증 실패: {after_chunks_count}개 데이터가 남아있음")
                else:
                    logger.info(f"[삭제 후] meeting_chunk: 0개 남음")
                    logger.info(f"✅ Vector DB (meeting_chunk) 삭제 검증 성공: 모든 데이터가 삭제되었습니다.")
            else:
                logger.info(f"[삭제 전] meeting_chunk: 0개")
                logger.info(f"ℹ️ Vector DB (meeting_chunk)에 meeting_id={meeting_id} 데이터 없음")

            logger.info("=" * 70)

        except Exception as e:
            logger.error(f"❌ Vector DB (meeting_chunk) 삭제 중 오류: {e}")
            import traceback
            traceback.print_exc()

        # 4. Vector DB subtopic 삭제
        deleted_subtopic_count = 0
        before_subtopic_count = 0
        after_subtopic_count = 0
        try:
            logger.info(f"\n📊 [Vector DB Subtopic 삭제 검증 시작] meeting_id = {meeting_id}")
            logger.info("=" * 70)

            # LangChain vectorstore의 underlying collection 사용
            subtopic_collection = self.vectorstores['subtopic']._collection

            # 삭제 전 전체 데이터 개수 확인 (limit 없이 조회)
            before_delete = subtopic_collection.get(where={"meeting_id": meeting_id})
            if before_delete and before_delete.get('ids'):
                before_subtopic_count = len(before_delete['ids'])
                logger.info(f"[삭제 전] meeting_subtopic: {before_subtopic_count}개")
                logger.info("-" * 70)

                # 삭제 실행
                subtopic_collection.delete(where={"meeting_id": meeting_id})
                logger.info(f"[삭제 수행] meeting_subtopic: {before_subtopic_count}개 삭제 시도")
                deleted_subtopic_count = before_subtopic_count

                logger.info("-" * 70)

                # 삭제 후 확인
                after_delete = subtopic_collection.get(where={"meeting_id": meeting_id})
                if after_delete and after_delete.get('ids'):
                    after_subtopic_count = len(after_delete['ids'])
                    logger.info(f"[삭제 후] meeting_subtopic: {after_subtopic_count}개 남음")
                    logger.warning(f"⚠️ Vector DB (meeting_subtopic) 삭제 검증 실패: {after_subtopic_count}개 데이터가 남아있음")
                else:
                    logger.info(f"[삭제 후] meeting_subtopic: 0개 남음")
                    logger.info(f"✅ Vector DB (meeting_subtopic) 삭제 검증 성공: 모든 데이터가 삭제되었습니다.")
            else:
                logger.info(f"[삭제 전] meeting_subtopic: 0개")
                logger.info(f"ℹ️ Vector DB (meeting_subtopic)에 meeting_id={meeting_id} 데이터 없음")

            logger.info("=" * 70)

        except Exception as e:
            logger.error(f"❌ Vector DB (meeting_subtopic) 삭제 중 오류: {e}")
            import traceback
            traceback.print_exc()

        # 5. 미디어 파일 삭제 (오디오 또는 비디오)
        logger.info(f"\n📊 [미디어 파일 삭제 검증 시작] meeting_id = {meeting_id}")
        logger.info("=" * 70)

        audio_deleted = False

        if audio_file:
            audio_path = os.path.join(self.upload_folder, audio_file)

            if os.path.exists(audio_path):
                logger.info(f"[삭제 전] 미디어 파일 존재: {audio_file}")
                logger.info(f"           경로: {audio_path}")
                logger.info("-" * 70)

                os.remove(audio_path)
                logger.info(f"[삭제 수행] 미디어 파일 삭제 시도: {audio_file}")

                logger.info("-" * 70)

                if not os.path.exists(audio_path):
                    logger.info(f"[삭제 후] 미디어 파일 없음")
                    logger.info(f"✅ 미디어 파일 삭제 검증 성공: 파일이 삭제되었습니다.")
                    audio_deleted = True
                else:
                    logger.info(f"[삭제 후] 미디어 파일 여전히 존재")
                    logger.warning(f"⚠️ 미디어 파일 삭제 검증 실패: 파일이 남아있습니다.")
            else:
                logger.info(f"[삭제 전] 미디어 파일 없음: {audio_file}")
                logger.info(f"ℹ️ 미디어 파일이 존재하지 않습니다.")
        else:
            logger.info(f"[건너뜀] audio_file 정보 없음")
            logger.info(f"ℹ️ audio_file을 찾을 수 없어 파일 삭제를 건너뜁니다.")

        logger.info("=" * 70)

        # 최종 요약
        logger.info(f"\n{'=' * 70}")
        logger.info(f"🎉 [삭제 작업 최종 요약] meeting_id = {meeting_id}")
        logger.info("=" * 70)
        logger.info(f"✓ SQLite meeting_dialogues: {deleted_sqlite['dialogues']}개 삭제")
        logger.info(f"✓ SQLite meeting_minutes: {deleted_sqlite['minutes']}개 삭제")
        logger.info(f"✓ SQLite meeting_shares: {deleted_sqlite.get('shares', 0)}개 삭제")
        logger.info(f"✓ Vector DB meeting_chunk: {deleted_chunks_count}개 삭제")
        logger.info(f"✓ Vector DB meeting_subtopic: {deleted_subtopic_count}개 삭제")
        logger.info(f"✓ 미디어 파일 (오디오/비디오): {'삭제됨' if audio_deleted else '없음/실패'}")
        logger.info("=" * 70 + "\n")

        return {
            "success": True,
            "message": "회의 데이터가 성공적으로 삭제되었습니다.",
            "deleted": {
                "sqlite_dialogues": deleted_sqlite["dialogues"],
                "sqlite_minutes": deleted_sqlite["minutes"],
                "sqlite_shares": deleted_sqlite.get("shares", 0),
                "vector_chunks": deleted_chunks_count,
                "vector_subtopic": deleted_subtopic_count,
                "audio_file": audio_file if audio_deleted else None
            }
        }

    def _update_collection_metadata(self, collection_name: str, meeting_id: str, field_name: str, new_value: str) -> int:
        """
        단일 ChromaDB 컬렉션의 메타데이터 필드를 업데이트하는 헬퍼

        Args:
            collection_name: 컬렉션 키 ('chunks' 또는 'subtopic')
            meeting_id: 회의 ID
            field_name: 업데이트할 메타데이터 필드명
            new_value: 새로운 값

        Returns:
            업데이트된 문서 수
        """
        collection = self.client.get_collection(name=self.COLLECTION_NAMES[collection_name])
        results = collection.get(where={"meeting_id": meeting_id})
        ids = results['ids']

        if not ids:
            logger.info(f"   ℹ️ {self.COLLECTION_NAMES[collection_name]}: 업데이트할 문서 없음")
            return 0

        updated_metadatas = []
        for metadata in results['metadatas']:
            updated_metadata = metadata.copy()
            updated_metadata[field_name] = new_value
            updated_metadatas.append(updated_metadata)

        collection.update(ids=ids, metadatas=updated_metadatas)
        count = len(ids)
        logger.info(f"   ✅ {self.COLLECTION_NAMES[collection_name]}: {count}개 문서의 {field_name} 업데이트 완료")
        return count

    def _update_metadata_field(self, meeting_id: str, chunk_field: str, subtopic_field: str, new_value: str) -> dict:
        """
        chunks와 subtopic 양쪽 컬렉션의 메타데이터를 업데이트하는 공통 메서드

        Args:
            meeting_id: 회의 ID
            chunk_field: chunks 컬렉션의 메타데이터 필드명
            subtopic_field: subtopic 컬렉션의 메타데이터 필드명
            new_value: 새로운 값

        Returns:
            dict: {'success': bool, 'updated_chunks': int, 'updated_subtopics': int}
        """
        logger.info(f"📊 [ChromaDB 메타데이터 업데이트] meeting_id={meeting_id}, field={chunk_field}/{subtopic_field}")

        updated_chunks = 0
        updated_subtopics = 0

        try:
            updated_chunks = self._update_collection_metadata('chunks', meeting_id, chunk_field, new_value)
            updated_subtopics = self._update_collection_metadata('subtopic', meeting_id, subtopic_field, new_value)

            logger.info(f"✅ ChromaDB 메타데이터 업데이트 완료: chunks={updated_chunks}, subtopics={updated_subtopics}")

            return {
                'success': True,
                'updated_chunks': updated_chunks,
                'updated_subtopics': updated_subtopics
            }

        except Exception as e:
            logger.error(f"❌ ChromaDB 메타데이터 업데이트 실패: {e}")
            return {
                'success': False,
                'error': str(e),
                'updated_chunks': updated_chunks,
                'updated_subtopics': updated_subtopics
            }

    def update_metadata_title(self, meeting_id: str, new_title: str) -> dict:
        """meeting_id의 모든 문서의 제목 메타데이터를 업데이트합니다."""
        return self._update_metadata_field(meeting_id, 'title', 'meeting_title', new_title)

    def update_metadata_date(self, meeting_id: str, new_date: str) -> dict:
        """meeting_id의 모든 문서의 날짜 메타데이터를 업데이트합니다."""
        return self._update_metadata_field(meeting_id, 'meeting_date', 'meeting_date', new_date)



# --- 싱글톤 인스턴스 생성 ---
# DB 파일은 minute_ai/database/vector_db 경로에 저장됩니다.
# vector_db_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'vector_db')
upload_folder_path = os.path.join(os.path.dirname(__file__), '..', 'uploads')
vdb_manager = VectorDBManager(upload_folder=upload_folder_path)
