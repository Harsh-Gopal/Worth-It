/**
 * Tests for the App version display in the sidebar.
 *
 * Verifies that:
 * 1. A version string is rendered in the sidebar (not undefined or empty)
 * 2. The rendered version matches the injected __APP_VERSION__ constant
 * 3. The version is shown in a semantically correct location (sidebar footer)
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';

// We mock heavy child pages to keep the test light
vi.mock('./pages/Monitoring', () => ({ default: () => <div data-testid="monitoring-page" /> }));
vi.mock('./pages/TrackHistory', () => ({ default: () => <div data-testid="history-page" /> }));
vi.mock('./pages/Settings', () => ({ default: () => <div data-testid="settings-page" /> }));
vi.mock('./components/branding/WorthItLogo', () => ({
  default: () => <div data-testid="worth-it-logo" />,
}));
vi.mock('./components/auth/AuthModal', () => ({ AuthModal: () => null }));

// Import App *after* mocks are set up
import App from './App';

beforeEach(() => {
  // Mock localStorage — needed by App's theme initializer and ProductSearch
  const store: Record<string, string> = {};
  Object.defineProperty(window, 'localStorage', {
    value: {
      getItem: vi.fn((key: string) => store[key] ?? null),
      setItem: vi.fn((key: string, val: string) => { store[key] = val; }),
      removeItem: vi.fn((key: string) => { delete store[key]; }),
      clear: vi.fn(() => { Object.keys(store).forEach(k => delete store[k]); }),
    },
    writable: true,
  });

  // Mock window.matchMedia — needed by App's theme initializer
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: vi.fn().mockImplementation((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  });

  // Mock fetch for the auth status check on mount
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
    ok: true,
    json: async () => ({ is_unlocked: true, security_enabled: false }),
  }));
});

describe('App version display', () => {
  it('renders a version string in the sidebar', () => {
    render(<App />);

    // __APP_VERSION__ is set to 'Version 0.999' in vitest.config.ts
    const versionEl = screen.getByText('Version 0.999');
    expect(versionEl).toBeInTheDocument();
  });

  it('version element is within the sidebar nav element', () => {
    const { container } = render(<App />);

    const nav = container.querySelector('nav');
    expect(nav).not.toBeNull();

    // The version text should be inside the nav
    expect(nav!.textContent).toContain('Version 0.999');
  });

  it('version text matches the expected format', () => {
    render(<App />);
    const versionEl = screen.getByText(/^Version (0\.\d+|test|999|Dev)/);
    expect(versionEl.textContent?.trim()).not.toBe('');
  });
});
