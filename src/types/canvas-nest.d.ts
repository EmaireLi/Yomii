declare module 'canvas-nest.js' {
  interface CanvasNestOptions {
    color?: string
    pointColor?: string
    opacity?: number
    zIndex?: number
    count?: number
    dist?: number
    lineWidth?: number
  }

  export default class CanvasNest {
    constructor(el: HTMLElement, options?: CanvasNestOptions)
    destroy(): void
  }
}
