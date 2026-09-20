import React from 'react';
import {
  ProteinFallback,
  BeautyFallback,
  BabyCareFallback,
  PetCareFallback,
  ElectronicsFallback,
  HomeKitchenFallback,
  FreshFallback,
  ChocolateFallback,
  GeneralProductFallback
} from '../components/icons/category';

export function resolveCategoryFallback(category?: string, productName?: string): React.ComponentType<React.SVGProps<SVGSVGElement>> {
  const c = (category || '').toLowerCase();
  const n = (productName || '').toLowerCase();

  const combinedStr = `${c} ${n}`;

  if (
    combinedStr.includes('protein') ||
    combinedStr.includes('sports nutrition') ||
    combinedStr.includes('whey') ||
    combinedStr.includes('mass gainer') ||
    combinedStr.includes('bcaa') ||
    combinedStr.includes('creatine')
  ) {
    return ProteinFallback;
  }

  if (
    combinedStr.includes('beauty') ||
    combinedStr.includes('personal care') ||
    combinedStr.includes('grooming') ||
    combinedStr.includes('shampoo') ||
    combinedStr.includes('face wash') ||
    combinedStr.includes('serum') ||
    combinedStr.includes('moisturizer')
  ) {
    return BeautyFallback;
  }

  if (
    combinedStr.includes('baby') ||
    combinedStr.includes('diaper') ||
    combinedStr.includes('wipes') ||
    combinedStr.includes('lotion')
  ) {
    return BabyCareFallback;
  }

  if (
    combinedStr.includes('pet') ||
    combinedStr.includes('dog food') ||
    combinedStr.includes('cat food') ||
    combinedStr.includes('treats')
  ) {
    return PetCareFallback;
  }

  if (
    combinedStr.includes('electronics') ||
    combinedStr.includes('phone') ||
    combinedStr.includes('earbuds') ||
    combinedStr.includes('mobile')
  ) {
    return ElectronicsFallback;
  }

  if (
    combinedStr.includes('home') ||
    combinedStr.includes('kitchen') ||
    combinedStr.includes('household') ||
    combinedStr.includes('cleaning')
  ) {
    return HomeKitchenFallback;
  }

  if (
    combinedStr.includes('fresh') ||
    combinedStr.includes('fruit') ||
    combinedStr.includes('vegetable') ||
    combinedStr.includes('apple') ||
    combinedStr.includes('banana') ||
    combinedStr.includes('tomato') ||
    combinedStr.includes('spinach')
  ) {
    return FreshFallback;
  }

  if (
    combinedStr.includes('chocolate') ||
    combinedStr.includes('confectionery') ||
    combinedStr.includes('cocoa') ||
    combinedStr.includes('candy')
  ) {
    return ChocolateFallback;
  }

  return GeneralProductFallback;
}
