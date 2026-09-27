import React, { useState } from 'react';
import { Package } from 'lucide-react';

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
    return (
      <Package
        className={fallbackClassName || className}
        style={{ ...style, opacity: 0.5, padding: "8px" }}
        strokeWidth={1.5}
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
      referrerPolicy="no-referrer"
      onError={() => setHasError(true)}
      {...props}
    />
  );
}
