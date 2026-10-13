const gallery=document.getElementById('gallery');
const escapeHtml=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const labels={line:'LINE TRACE',scatter:'SCATTER',heatmap:'PAPER / HEATMAP'};
const modal=document.getElementById('viewer');
async function init(){
 try{
  const response=await fetch('cases.json');if(!response.ok)throw new Error('HTTP '+response.status);
  const data=await response.json();document.getElementById('macro').innerHTML=data.macro_accuracy_pct.toFixed(2)+'<span>%</span>';
  for(const c of data.cases){
   const id=encodeURIComponent(c.id),m=c.metrics;
   const scored=Number.isFinite(m.accuracy_pct);
   const note=!scored?'尚无独立数值参考，暂不报告准确率。只提取蓝色实测 NEE；估算曲线和标准差带不作为观测值。':c.group==='flux'?`PDF 矢量路径独立核验 · 误差 ≤ y 轴量程 1% · 覆盖 ${m.coverage_pct.toFixed(2)}%。${m.accuracy_pct<90?'密集交叉困难案例，尚未达到 90%。':'本面板通过 90% 阈值。'}<br>评分衡量图形还原，非原始观测误差。`:c.kind==='heatmap'?`舍入感知 ${m.accuracy_pct.toFixed(2)}% · 原始严格分数 ${m.raw_within_1pct_range_pct.toFixed(2)}%<br>MAE ${m.mae.toFixed(4)} · ${m.numeric_cells} 数值单元 + ${m.endpoint_censored_cells} 饱和区间；不计入宏平均。`:c.kind==='line'?`误差 ≤ y 轴量程 1% · 覆盖率 ${m.coverage_pct.toFixed(2)}% · 漏点计入分母。`:`F1 @ 1% 坐标距离 · 精确率 ${m.precision_pct.toFixed(2)}% · 召回率 ${m.recall_pct.toFixed(2)}%。`;
   const delta=scored&&m.unmasked?m.accuracy_pct-m.unmasked.accuracy_pct:0;
   const card=document.createElement('article');card.className='card';card.dataset.kind=c.kind;card.dataset.group=c.group||'other';card.dataset.status=!scored?'unscored':m.accuracy_pct<90?'challenge':'scored';
   card.innerHTML=`<div class="card-top"><div><span class="case-tag">${escapeHtml(c.id)} / ${labels[c.kind]} / ${escapeHtml(c.source_label)}</span><h3>${escapeHtml(c.title)}</h3></div><div class="accuracy ${!scored?'unscored':m.accuracy_pct<90?'challenge':''}"><strong>${scored?m.accuracy_pct.toFixed(2)+'<span>%</span>':'未评分'}</strong><small>${!scored?'NO REFERENCE':c.group==='flux'?'PDF GEOMETRY':c.kind==='scatter'?'F1 SCORE':c.kind==='heatmap'?'ROUNDING-AWARE':'WITHIN 1% RANGE'}</small></div></div><div class="card-canvas"><div class="image-cell"><span class="image-label">ORIGINAL</span><img loading="lazy" src="cases/${id}/original.png" alt="${escapeHtml(c.title)}：原始图表" tabindex="0"></div><div class="image-cell"><span class="image-label mode-label">EXTRACTION OVERLAY</span><img loading="lazy" class="result-image" src="cases/${id}/overlay.png" alt="${escapeHtml(c.title)}：提取覆盖图" tabindex="0"></div></div><div class="card-controls"><div class="modes" role="group" aria-label="${escapeHtml(c.title)} 展示模式"><button data-image="overlay" class="active" aria-pressed="true">提取覆盖</button><button data-image="legend-overlay" aria-pressed="false">图例遮罩</button><button data-image="recreated" aria-pressed="false">CSV 重绘</button></div><a class="download" href="cases/${id}/data.csv" download>CSV ↓</a></div><p class="metric-note">${note}</p>${c.doi?`<p class="source-note"><a href="https://doi.org/${escapeHtml(c.doi)}" target="_blank" rel="noopener">${escapeHtml(c.doi)} ↗</a> · ${escapeHtml(c.license)} · <a href="cases/${id}/provenance.json">来源记录</a>${c.context_image?` · <a href="cases/${id}/${c.context_image}" target="_blank" rel="noopener">完整原图</a>`:''}</p>`:''}<div class="card-links"><a href="cases/${id}/comparison.png" target="_blank" rel="noopener">并排对比 ↗</a><a href="cases/${id}/metrics.json">评分 JSON ↗</a><a href="cases/${id}/report.json">提取报告 ↗</a>${delta>.01?`<span class="delta">遮罩 +${delta.toFixed(2)}pp</span>`:''}</div>`;
   card.querySelectorAll('[data-image]').forEach(button=>button.addEventListener('click',()=>{
    card.querySelectorAll('[data-image]').forEach(b=>{b.classList.toggle('active',b===button);b.setAttribute('aria-pressed',b===button?'true':'false')});
    card.querySelector('.result-image').src=`cases/${id}/${button.dataset.image}.png`;
    card.querySelector('.result-image').alt=`${c.title}：${button.textContent}`;
    card.querySelector('.mode-label').textContent={overlay:'EXTRACTION OVERLAY','legend-overlay':'LEGEND EXCLUSION',recreated:'RECREATED FROM CSV'}[button.dataset.image];
   }));
   card.querySelectorAll('.image-cell img').forEach(img=>{
    function open(){modal.querySelector('img').src=img.src;modal.querySelector('img').alt=img.alt;modal.querySelector('p').textContent=img.alt;modal.showModal()}
    img.addEventListener('click',open);img.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();open()}});
   });gallery.append(card);
  }
 }catch(error){gallery.innerHTML='<p class="error">案例加载失败。请刷新页面，或在 GitHub README 查看静态对比图。</p>';console.error(error)}
}
document.querySelectorAll('[data-filter]').forEach(button=>button.addEventListener('click',()=>{
 document.querySelectorAll('[data-filter]').forEach(b=>{b.classList.toggle('active',b===button);b.setAttribute('aria-pressed',b===button?'true':'false')});
 gallery.querySelectorAll('.card').forEach(card=>card.hidden=button.dataset.filter!=='all'&&card.dataset.kind!==button.dataset.filter&&card.dataset.group!==button.dataset.filter&&card.dataset.status!==button.dataset.filter);
}));
document.getElementById('close-viewer').addEventListener('click',()=>modal.close());
modal.addEventListener('click',e=>{if(e.target===modal)modal.close()});
document.getElementById('copy').addEventListener('click',async e=>{try{await navigator.clipboard.writeText('git clone https://github.com/GISWLH/digitizer.git');e.target.textContent='已复制';setTimeout(()=>e.target.textContent='复制',1800)}catch{e.target.textContent='请选中复制'}});
init();

async function initAi(){
 const target=document.getElementById('ai-gallery');
 try{
  const response=await fetch('ai/results.json');if(!response.ok)throw new Error('HTTP '+response.status);
  const data=await response.json(),order=['a02','a03','a01'];
  for(const id of order){
   const m=data.cases.find(c=>c.id===id),scored=Number.isFinite(m.accuracy_pct);
   const title={a01:'同色圆点填色，先在原图验证形状',a02:'真实盐沼 NEE：图例、色带与估算线退场',a03:'Nano Banana：只选中 Stein 蓝线'}[id];
   const card=document.createElement('article');card.className='ai-story';
   const modes=[['process','全流程'],['edited-aligned','AI 填色'],['support-overlay','原图复核'],[id==='a01'?'overlay':'grid-overlay',id==='a01'?'提取覆盖':'网格采样'],['recreated','CSV 重绘']];
   card.innerHTML=`<div class="card-top"><div><span class="case-tag">${id.toUpperCase()} / ${escapeHtml(m.model)} / APIYI</span><h3>${title}</h3></div><div class="accuracy ${scored?'':'unscored'}"><strong>${scored?m.accuracy_pct.toFixed(2)+'%':'未评分'}</strong><small>${id==='a01'?'F1 / 15 OF 16':id==='a03'?'PDF / 391 OF 401':'NO REFERENCE'}</small></div></div><img class="ai-picture" src="ai/${id}/process.png" alt="${title}：完整提取过程" loading="lazy" tabindex="0"><div class="card-controls"><div class="modes" role="group" aria-label="${title} 过程步骤">${modes.map(([name,label],i)=>`<button data-ai-step="${name}" class="${i===0?'active':''}" aria-pressed="${i===0}">${label}</button>`).join('')}</div><a class="download" href="ai/${id}/data.csv" download>CSV ↓</a></div><p>${scored?`同目标直接 THU 基线 ${m.baseline_accuracy_pct.toFixed(2)}%；本例没有精度提升。${id==='a03'?'单独评价 Stein，不与双曲线评分混用。':'漏掉的 1 个观测点仍计入分母。'}`:'无独立作者数值，保留 759 列提取值；直接 THU 为 792 列。颜色支持比例不作为准确率。'}</p><div class="card-links"><a href="ai/${id}/prompt.txt">完整 prompt ↗</a><a href="ai/${id}/generated.png" target="_blank" rel="noopener">原始返回图 ↗</a><a href="ai/${id}/metrics.json">评分 JSON ↗</a><a href="ai/${id}/ai-report.json">完整报告 ↗</a>${id!=='a01'?`<a href="ai/${id}/grid.csv" download>网格 CSV ↓</a>`:''}</div>${id==='a03'?'<p>Veenendaal et al. (2007), Fig. 11 · 图件及衍生成果 CC BY-NC-SA 2.5</p>':id==='a02'?'<p>Mayen et al. (2024), Fig. 5a · CC BY 4.0</p>':'<p>用户提供书稿 · 月度 RMSE 面板 · 与 r03 相同原图</p>'}`;
   card.querySelectorAll('[data-ai-step]').forEach(b=>b.addEventListener('click',()=>{
    card.querySelectorAll('[data-ai-step]').forEach(x=>{x.classList.toggle('active',x===b);x.setAttribute('aria-pressed',String(x===b))});
    const img=card.querySelector('.ai-picture');img.src=`ai/${id}/${b.dataset.aiStep}.png`;img.alt=`${title}：${b.textContent}`;
   }));
   const img=card.querySelector('.ai-picture');function open(){modal.querySelector('img').src=img.src;modal.querySelector('img').alt=img.alt;modal.querySelector('p').textContent=img.alt;modal.showModal()}
   img.addEventListener('click',open);img.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();open()}});
   target.append(card);
  }
 }catch(error){target.innerHTML='<p class="error">AI 案例加载失败，请查看 GitHub README 的静态过程图。</p>';console.error(error)}
}
initAi();
