export type ExportFormat = 'svg' | 'png';

export interface ChartExportOptions {
  filenameBase: string;
  format: ExportFormat;
  dpi?: number;
  widthMm?: number;
}

const SVG_NS = 'http://www.w3.org/2000/svg';
const DEFAULT_DPI = 600;
const DEFAULT_WIDTH_MM = 178;

const sanitizeFilename = (value: string): string =>
  value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '') || 'chart';

const downloadBlob = (blob: Blob, filename: string) => {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};

const getPrimarySvg = (root: HTMLElement): SVGSVGElement | null => {
  return (
    root.querySelector('svg.publication-svg') ||
    root.querySelector('svg.recharts-surface') ||
    root.querySelector('svg')
  ) as SVGSVGElement | null;
};

const getSvgDimensions = (svg: SVGSVGElement): { width: number; height: number } => {
  const viewBox = svg.getAttribute('viewBox');
  if (viewBox) {
    const parts = viewBox.split(/\s+|,/).map(Number).filter(Number.isFinite);
    if (parts.length === 4 && parts[2] > 0 && parts[3] > 0) {
      return { width: parts[2], height: parts[3] };
    }
  }

  const attrWidth = Number(svg.getAttribute('width'));
  const attrHeight = Number(svg.getAttribute('height'));
  if (Number.isFinite(attrWidth) && Number.isFinite(attrHeight) && attrWidth > 0 && attrHeight > 0) {
    return { width: attrWidth, height: attrHeight };
  }

  const rect = svg.getBoundingClientRect();
  return {
    width: Math.max(1, rect.width || 1200),
    height: Math.max(1, rect.height || 760),
  };
};

export const buildExportSvgString = (root: HTMLElement): { svgText: string; width: number; height: number } => {
  const sourceSvg = getPrimarySvg(root);
  if (!sourceSvg) {
    throw new Error('No SVG chart found to export.');
  }

  const { width, height } = getSvgDimensions(sourceSvg);
  const clone = sourceSvg.cloneNode(true) as SVGSVGElement;
  clone.setAttribute('xmlns', SVG_NS);
  clone.setAttribute('width', String(width));
  clone.setAttribute('height', String(height));
  clone.setAttribute('viewBox', clone.getAttribute('viewBox') || `0 0 ${width} ${height}`);
  clone.setAttribute('role', 'img');
  clone.style.background = '#ffffff';
  clone.style.fontFamily = 'Arial, Helvetica, sans-serif';

  const style = document.createElementNS(SVG_NS, 'style');
  style.textContent = `
    text { font-family: Arial, Helvetica, sans-serif; letter-spacing: 0; }
    .recharts-cartesian-axis-tick-value, .recharts-legend-item-text { fill: #222; font-size: 11px; }
    .recharts-label { fill: #222; font-size: 12px; }
    .recharts-cartesian-grid line { stroke: #d8d8d8; stroke-width: 0.7; }
    .recharts-cartesian-axis-line, .recharts-cartesian-axis-tick-line { stroke: #333; stroke-width: 0.8; }
  `;
  clone.insertBefore(style, clone.firstChild);

  const background = document.createElementNS(SVG_NS, 'rect');
  background.setAttribute('x', '0');
  background.setAttribute('y', '0');
  background.setAttribute('width', String(width));
  background.setAttribute('height', String(height));
  background.setAttribute('fill', '#ffffff');
  clone.insertBefore(background, style.nextSibling);

  const serializer = new XMLSerializer();
  const svgText = serializer.serializeToString(clone);
  return { svgText, width, height };
};

export const exportChart = async (root: HTMLElement, options: ChartExportOptions) => {
  const { svgText, width, height } = buildExportSvgString(root);
  const filenameBase = sanitizeFilename(options.filenameBase);

  if (options.format === 'svg') {
    downloadBlob(new Blob([svgText], { type: 'image/svg+xml;charset=utf-8' }), `${filenameBase}.svg`);
    return;
  }

  const dpi = options.dpi || DEFAULT_DPI;
  const widthMm = options.widthMm || DEFAULT_WIDTH_MM;
  const targetWidth = Math.round((widthMm / 25.4) * dpi);
  const targetHeight = Math.round(targetWidth * (height / width));

  const svgBlob = new Blob([svgText], { type: 'image/svg+xml;charset=utf-8' });
  const url = URL.createObjectURL(svgBlob);
  try {
    const image = new Image();
    image.decoding = 'async';
    await new Promise<void>((resolve, reject) => {
      image.onload = () => resolve();
      image.onerror = () => reject(new Error('Failed to render SVG for PNG export.'));
      image.src = url;
    });

    const canvas = document.createElement('canvas');
    canvas.width = targetWidth;
    canvas.height = targetHeight;
    const ctx = canvas.getContext('2d');
    if (!ctx) {
      throw new Error('Canvas is not available.');
    }
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, targetWidth, targetHeight);
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = 'high';
    ctx.drawImage(image, 0, 0, targetWidth, targetHeight);

    const pngBlob = await new Promise<Blob>((resolve, reject) => {
      canvas.toBlob((blob) => {
        if (blob) resolve(blob);
        else reject(new Error('Failed to create PNG blob.'));
      }, 'image/png');
    });
    downloadBlob(pngBlob, `${filenameBase}_${dpi}dpi.png`);
  } finally {
    URL.revokeObjectURL(url);
  }
};
