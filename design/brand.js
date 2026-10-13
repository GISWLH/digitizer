import {convertToExcalidrawElements,exportToSvg,exportToBlob,serializeAsJSON} from '@excalidraw/excalidraw';
const ink='#203b33',paper='#fffdf5',green='#cdeaac',pink='#e896ac',blue='#47878b';let sequence=1;
function el(type,x,y,width,height,extra={}){return {type,x,y,width,height,strokeColor:ink,backgroundColor:'transparent',fillStyle:'solid',strokeWidth:2,roughness:1.4,opacity:100,seed:1000+sequence++,versionNonce:2,...extra}}
const box=(x,y,w,h,extra={})=>el('rectangle',x,y,w,h,{roundness:{type:3},...extra});
const txt=(x,y,text,fontSize=24,extra={})=>el('text',x,y,0,0,{text,fontSize,fontFamily:1,strokeWidth:1,roughness:1,...extra});
const line=(x,y,points,extra={})=>el('line',x,y,Math.max(...points.map(p=>p[0])),Math.max(...points.map(p=>p[1])),{points,...extra});
const arrow=(x,y,points)=>el('arrow',x,y,points.at(-1)[0],points.at(-1)[1],{points,endArrowhead:'arrow',roughness:1.8});
const dot=(x,y,r=6,color=ink)=>el('ellipse',x-r,y-r,2*r,2*r,{strokeColor:color,backgroundColor:color,roughness:1});
const banner=[box(0,0,1280,670,{backgroundColor:paper,strokeColor:paper,roughness:0,roundness:null}),txt(65,45,'digitizer',72),txt(67,136,'Figures in. Evidence out.',30),txt(805,68,'A little mask.\nA lot less confusion.',29,{strokeColor:'#687c58'}),line(809,144,[[0,0],[243,6]],{strokeColor:pink,strokeWidth:6,opacity:70}),box(64,245,314,282,{backgroundColor:'#ffffff'}),box(482,245,314,282,{backgroundColor:'#ffffff'}),box(899,245,314,282,{backgroundColor:'#ffffff'}),txt(82,209,'01 / PAPER FIGURE',19),txt(504,209,'02 / PRECISE MASK',19),txt(920,209,'03 / AUDITABLE CSV',19),arrow(393,378,[[0,0],[66,0]]),arrow(810,378,[[0,0],[69,0]])];
for(const offset of [0,420]){
 banner.push(line(99+offset,295,[[0,0],[0,185],[240,185]],{strokeWidth:1.8}),line(103+offset,446,[[0,0],[24,-24],[47,-8],[67,-71],[94,-111],[123,-70],[149,-103],[171,-90],[197,-137],[228,-113]],{strokeColor:blue,strokeWidth:3}));
 banner.push(box(119+offset,267,146,59,{backgroundColor:offset?'#f9d4de':'#ffffff',strokeColor:offset?pink:'#8b9a91',strokeStyle:offset?'dashed':'solid',roughness:1}),line(132+offset,286,[[0,0],[31,0]],{strokeColor:blue,strokeWidth:3}),txt(172+offset,275,'NEE',18),line(132+offset,309,[[0,0],[31,0]],{strokeColor:'#6f8b4c',strokeWidth:2}),txt(172+offset,299,'GPP',18));
 if(offset)banner.push(line(570,275,[[0,0],[86,46]],{strokeColor:'#bc5473',strokeWidth:2}),line(570,321,[[0,0],[86,-46]],{strokeColor:'#bc5473',strokeWidth:2}));
}
banner.push(txt(514,544,'keep the visible curve',21,{strokeColor:blue}),txt(96,544,'legends look like data!',21,{strokeColor:'#a44a65'}),box(924,276,264,40,{backgroundColor:green,strokeColor:green,roughness:.5}),txt(938,283,'time     NEE     source',17));
for(let j=0;j<5;j++)banner.push(line(925,337+j*34,[[0,0],[262,0]],{strokeColor:'#bdc9b7',strokeWidth:1,roughness:.8}),txt(940,316+j*34,`${String(j*4).padStart(2,'0')}:00     ${['1.2','0.8','-4.1','-6.2','-2.0'][j]}      fig.5`,16,{strokeColor:'#50664f'}));
banner.push(txt(941,494,'+ masks + evidence',18,{strokeColor:'#617653'}),line(64,600,[[0,0],[1150,0]],{strokeColor:'#b1c2a4',strokeWidth:1}),txt(66,617,'Built on THU Digitizer',20),txt(710,617,'Original  →  Extract  →  Compare',20),txt(965,546,'values shown are schematic',14,{strokeColor:'#7e8977'}));
const logo=[box(0,0,256,256,{backgroundColor:paper,strokeColor:paper,roughness:0,roundness:null}),box(14,14,228,228,{strokeColor:ink,backgroundColor:green,strokeWidth:4}),line(55,49,[[0,0],[0,154],[151,154]],{strokeColor:ink,strokeWidth:7}),line(69,175,[[0,0],[23,-15],[23,-60],[32,-77],[58,-91],[98,-73],[115,-44],[101,-9],[58,7],[24,0]],{strokeColor:ink,strokeWidth:7}),box(147,47,61,34,{backgroundColor:'#f6c3d3',strokeColor:'#b7657d',strokeStyle:'dashed',strokeWidth:2,roughness:1.5}),line(156,55,[[0,0],[43,19]],{strokeColor:'#b7657d',strokeWidth:3}),dot(101,117,5,blue),dot(163,143,5,blue)];
const state={viewBackgroundColor:paper,exportBackground:true,exportWithDarkMode:false,exportEmbedScene:true};
for(const [name,skeleton] of [['banner',banner],['icon',logo]]){
 const elements=convertToExcalidrawElements(skeleton);const svg=await exportToSvg({elements,appState:state,files:null,exportPadding:0});document.getElementById('preview').append(svg);
 for(const [ext,data] of [['svg',svg.outerHTML],['excalidraw',serializeAsJSON(elements,state,{},'local')],['png',await exportToBlob({elements,appState:state,files:null,mimeType:'image/png',exportPadding:0})]]){const r=await fetch('/save/'+name+'.'+ext,{method:'POST',body:data});if(!r.ok)throw Error('Save failed: '+name+'.'+ext)}
}
document.getElementById('status').textContent='Exported banner + logo: SVG, PNG and editable Excalidraw scenes.';window.brandReady=true;
