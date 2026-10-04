import { copyFile, mkdir, readdir } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const root = fileURLToPath(new URL('..', import.meta.url));
const destination = join(root, 'public', 'vad');
const vad = dirname(require.resolve('@ricky0123/vad-web'));
const ort = dirname(require.resolve('onnxruntime-web'));
await mkdir(destination, { recursive: true });
const files = [
  ...['vad.worklet.bundle.min.js', 'silero_vad_v5.onnx'].map(name => [vad, name]),
  ...(await readdir(ort)).filter(name => /^ort-wasm.*\.(wasm|mjs)$/.test(name)).map(name => [ort, name]),
];
if (files.length < 4) throw new Error('ONNX runtime WASM/module assets are missing');
for (const [directory, name] of files) await copyFile(join(directory, name), join(destination, name));
console.log('Copied ' + files.length + ' pinned VAD/runtime assets to public/vad');
