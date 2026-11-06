// Tesseract runs locally. The English model is bundled; no remote fetches.
const path=require('node:path');
const {createWorker}=require('tesseract.js');
(async()=>{
 const root=path.resolve(__dirname,'..');
 const worker=await createWorker('eng',1,{langPath:path.join(root,'data'),gzip:false,cacheMethod:'none',logger:()=>{}});
 try{const {data}=await worker.recognize(process.argv[2]);process.stdout.write(data.text)}finally{await worker.terminate()}
})().catch(()=>{process.stderr.write('Local OCR failed\n');process.exitCode=1});
