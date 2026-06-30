declare module 'markmap-lib' {
  export class Transformer {
    transform(markdown: string): { root: any };
  }
}

declare module 'markmap-view' {
  export class Markmap {
    static create(el: SVGElement, opts: any, root: any): Markmap;
    setData(root: any): void;
    fit(): void;
  }
}
