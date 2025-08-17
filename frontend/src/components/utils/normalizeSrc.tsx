// Helper to ensure image paths start with a leading slash
export const normalizeSrc = (src: string) => {
  if (!src.startsWith("/")) return "/" + src;

  return src;
};
