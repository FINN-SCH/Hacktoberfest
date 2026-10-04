/** Playback resolves on ended, rejects on blocked playback/error/stop. No silent resume. */
export class AudioPlayer {
  private context: AudioContext | null = null;
  private cancel: (() => void) | null = null;
  private generation = 0;

  async unlock(): Promise<void> {
    this.context ??= new AudioContext();
    await this.context.resume();
    if (this.context.state !== 'running') throw new Error('Audio playback needs a user gesture');
  }

  async play(blob: Blob): Promise<void> {
    this.stop();
    const generation = this.generation;
    const context = this.context;
    if (!context || context.state !== 'running') throw new Error('Start conversation to enable audio');
    const buffer = await context.decodeAudioData(await blob.arrayBuffer());
    if (generation !== this.generation) throw new DOMException('Playback cancelled', 'AbortError');
    const source = context.createBufferSource();
    source.buffer = buffer;
    source.connect(context.destination);
    return new Promise<void>((resolve, reject) => {
      const cleanup = () => { source.disconnect(); this.cancel = null; };
      this.cancel = () => { source.onended = null; source.stop(); cleanup(); reject(new DOMException('Playback cancelled', 'AbortError')); };
      source.onended = () => { cleanup(); resolve(); };
      try { source.start(); } catch (error) { cleanup(); reject(error); }
    });
  }

  stop(): void { this.generation++; this.cancel?.(); }
  async dispose(): Promise<void> {
    this.stop();
    const context = this.context;
    this.context = null;
    if (context && context.state !== 'closed') await context.close();
  }
}
