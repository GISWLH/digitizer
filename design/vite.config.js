import {defineConfig} from 'vite';
import fs from 'node:fs';
import path from 'node:path';
export default defineConfig({plugins:[{name:'save-brand',configureServer(server){server.middlewares.use('/save',async(req,res,next)=>{if(req.method!=='POST')return next();const name=req.url.slice(1);if(!/^(banner|icon)\.(svg|png|excalidraw)$/.test(name)){res.statusCode=400;return res.end()};let chunks=[];for await(const chunk of req)chunks.push(chunk);fs.writeFileSync(path.resolve('../docs/assets',name),Buffer.concat(chunks));res.end('saved')})}}]});
