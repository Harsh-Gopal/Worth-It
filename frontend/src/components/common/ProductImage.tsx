import React, { useState } from 'react';
import { resolveCategoryFallback } from '../../lib/categoryResolver';

interface ProductImageProps extends React.ImgHTMLAttributes<HTMLImageElement> {
  category?: string;
  productName?: string;
  fallbackClassName?: string;
}

export function ProductImage({
  src,
  alt,
  category,
  productName,
  className,
  style,
  fallbackClassName,
  ...props
}: ProductImageProps) {
  const [hasError, setHasError] = useState(false);

  // If no source or image errored, show fallback
  if (!src || hasError) {
    const FallbackSVG = resolveCategoryFallback(category, productName || alt);
    return (
      <FallbackSVG
        className={fallbackClassName || className}
        style={style}
        aria-hidden="true"
      />
    );
  }

  return (
    <img
      src={src}
      alt={alt}
      className={className}
      style={style}
      onError={() => setHasError(true)}
      {...props}
    />
  );
}
