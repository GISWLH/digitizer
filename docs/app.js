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
   card.innerHTML=`<div class="card-top"><div><span class="case-tag">${escapeHtml(c.id)} / ${labels[c.kind]} / ${escapeHtml(c.source_label)}</span><h3>${escapeHtml(c.title)}</h3></div><div class="accuracy ${!scored?'unscored':m.accuracy_pct<90?'challenge':''}"><strong>${scored?m.accuracy_pct.toFixed(2)+'<span>%</span>':'未评分'}</strong><small>${!scored?'NO REFERENCE':c.group==='flux'?'PDF GEOMETRY':c.kind==='scatter'?'F1 SCORE':c.kind==='heatmap'?'ROUNDING-AWARE':'WITHIN 1% RANGE'}</small></div></div><div class="card-canvas"><div class="image-cell"><span class="image-label">ORIGINAL</span><img loading="lazy" src="cases/${id}/original.png" alt="${escapeHtml(c.title)}：原始图表" tabindex="0"></div><div class="image-cell"><span class="image-label mode-label">EXTRACTION OVERLAY</span><img loading="lazy" class="result-image" src="cases/${id}/overlay.png" alt="${escapeHtml(c.title)}：提取覆盖图" tabindex="0"></div></div><div class="card-controls"><div class="modes" role="group" aria-label="${escapeHtml(c.title)} 展示模式"><button data-image="overlay" class="active" aria-pressed="true">提取覆盖</button><button data-image="legend-overlay" aria-pressed="false">图例遮罩</button><button data-image="recreated" aria-pressed="false">CSV 重绘</button></div><a class="download" href="cases/${id}/data.csv" download>CSV ↓</a></div><p class="metric-note">${note}</p>${c.doi?`<p class="source-note"><a href="https://doi.org/${escapeHtml(c.doi)}" target="_blank" rel="noopener">${escapeHtml(c.doi)} ↗</a> · ${escapeHtml(c.license)} · <a href="cases/${id}/provenance.json">来源记录</a></p>`:''}<div class="card-links"><a href="cases/${id}/comparison.png" target="_blank" rel="noopener">并排对比 ↗</a><a href="cases/${id}/metrics.json">评分 JSON ↗</a><a href="cases/${id}/report.json">提取报告 ↗</a>${delta>.01?`<span class="delta">遮罩 +${delta.toFixed(2)}pp</span>`:''}</div>`;
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
