from flask import Blueprint, render_template
from utils.decorators import login_required

# Blueprint 생성
live_bp = Blueprint('live', __name__)

@live_bp.route('/record')
@login_required
def recorder():
    """
    실시간 녹음 페이지 (마이크 & 시스템 오디오)
    """
    return render_template('live/recorder.html')
