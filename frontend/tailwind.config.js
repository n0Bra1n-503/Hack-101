/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        // Literal 4-swatch palette (sky blue / periwinkle / lavender / pink),
        // used as-given for fills and backgrounds. They're too pale to read
        // as TEXT (~2:1 contrast on white), so every place that used to
        // color text with these now colors a background/fill/dot instead
        // and keeps the text itself in `ink` — see StatusBadge, MetricCard,
        // TrustScore, etc. `accent` is the one exception left readable as
        // text (links, buttons) since it's used that way throughout.
        canvas: '#F8F9FE',
        panel: '#FFFFFF',
        hairline: '#E4E8FB',
        ink: '#2B2438',
        inkMuted: '#7A7189',
        accent: '#9A57BD', // deepened lavender — the one color still used as text
        accentHover: '#833D9E',
        healthy: '#9BD8FA', // literal sky-blue swatch
        degrading: '#CBD9FA', // literal periwinkle swatch
        critical: '#FCDCD8', // literal pink swatch
      },
    },
  },
  plugins: [],
}
