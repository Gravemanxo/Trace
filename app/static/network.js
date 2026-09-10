(() => {
  const host = document.getElementById('network-canvas');
  const source = document.getElementById('network-data');
  if (!host || !source) return;
  const data = JSON.parse(source.textContent);
  if (!data.nodes.length) {
    host.hidden = true;
    document.getElementById('network-empty').hidden = false;
    return;
  }
  const ns = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(ns, 'svg');
  svg.setAttribute('viewBox', '0 0 1000 620');
  const stage = document.createElementNS(ns, 'g');
  svg.append(stage);
  host.append(svg);
  const center = { x: 500, y: 310 };
  const positions = new Map();
  const projects = data.nodes.filter((node) => node.type === 'project');
  data.nodes.forEach((node, index) => {
    if (node.type === 'project') {
      const i = projects.indexOf(node);
      const angle = (Math.PI * 2 * i) / Math.max(1, projects.length) - Math.PI / 2;
      positions.set(node.id, { x: center.x + Math.cos(angle) * 190, y: center.y + Math.sin(angle) * 190 });
    } else {
      const linked = data.edges.find((edge) => edge.target === node.id);
      const anchor = positions.get(linked?.source) || center;
      const angle = (index * 2.399) % (Math.PI * 2);
      positions.set(node.id, { x: anchor.x + Math.cos(angle) * 105, y: anchor.y + Math.sin(angle) * 105 });
    }
  });
  const edges = data.edges.map((edge) => {
    const line = document.createElementNS(ns, 'line');
    line.classList.add('network-edge');
    stage.append(line);
    return { ...edge, element: line };
  });
  const nodes = data.nodes.map((node) => {
    const group = document.createElementNS(ns, 'g');
    group.classList.add('network-node');
    group.dataset.type = node.type;
    const circle = document.createElementNS(ns, 'circle');
    circle.setAttribute('r', node.type === 'project' ? '18' : '12');
    const label = document.createElementNS(ns, 'text');
    label.setAttribute('x', '24');
    label.setAttribute('y', '4');
    label.textContent = node.label.length > 34 ? `${node.label.slice(0, 32)}…` : node.label;
    group.append(circle, label);
    group.addEventListener('dblclick', () => window.location.assign(node.url));
    stage.append(group);
    return { ...node, element: group };
  });
  const draw = () => {
    edges.forEach((edge) => {
      const start = positions.get(edge.source); const end = positions.get(edge.target);
      edge.element.setAttribute('x1', start.x); edge.element.setAttribute('y1', start.y);
      edge.element.setAttribute('x2', end.x); edge.element.setAttribute('y2', end.y);
    });
    nodes.forEach((node) => { const point = positions.get(node.id); node.element.setAttribute('transform', `translate(${point.x} ${point.y})`); });
  };
  let dragged = null;
  nodes.forEach((node) => node.element.addEventListener('pointerdown', (event) => { dragged = node; node.element.setPointerCapture(event.pointerId); }));
  svg.addEventListener('pointermove', (event) => {
    if (!dragged) return;
    const point = svg.createSVGPoint(); point.x = event.clientX; point.y = event.clientY;
    const local = point.matrixTransform(stage.getScreenCTM().inverse());
    positions.set(dragged.id, { x: local.x, y: local.y }); draw();
  });
  svg.addEventListener('pointerup', () => { dragged = null; });
  let scale = 1; let offsetX = 0; let offsetY = 0;
  svg.addEventListener('wheel', (event) => { event.preventDefault(); scale = Math.min(2.4, Math.max(.55, scale * (event.deltaY > 0 ? .9 : 1.1))); stage.setAttribute('transform', `translate(${offsetX} ${offsetY}) scale(${scale})`); }, { passive: false });
  let panStart = null;
  svg.addEventListener('pointerdown', (event) => { if (event.target === svg) panStart = { x: event.clientX - offsetX, y: event.clientY - offsetY }; });
  svg.addEventListener('pointermove', (event) => { if (panStart && !dragged) { offsetX = event.clientX - panStart.x; offsetY = event.clientY - panStart.y; stage.setAttribute('transform', `translate(${offsetX} ${offsetY}) scale(${scale})`); } });
  svg.addEventListener('pointerup', () => { panStart = null; });
  draw();
})();
