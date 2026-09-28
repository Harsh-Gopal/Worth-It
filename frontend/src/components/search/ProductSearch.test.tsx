import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';

import ProductSearch from './ProductSearch';
import '@testing-library/jest-dom';

vi.mock('./WishlistSection', () => ({
  default: () => <div data-testid="wishlist-section-mock" />
}));
vi.mock('./KeywordInput', () => ({
  default: () => <div data-testid="keyword-input-mock" />
}));
vi.mock('./CategorySelector', () => ({
  default: () => <div data-testid="category-selector-mock" />
}));

describe('ProductSearch Configuration Changes and Restart Tracking', () => {
  const mockOnSearch = vi.fn();
  const mockOnCancel = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: vi.fn(),
        setItem: vi.fn(),
        removeItem: vi.fn(),
        clear: vi.fn(),
      },
      writable: true,
    });
    window.localStorage.clear();
  });

  const defaultProps = {
    onSearch: mockOnSearch,
    isSearching: false,
    onCancel: mockOnCancel,
  };

  it('1. Start tracking -> button shows Stop Tracking', async () => {
    const { rerender } = render(<ProductSearch {...defaultProps} />);
    
    // Select platform
    // Swiggy is selected by default based on initial state, but let's make sure
    // Swiggy is selected by default based on initial state, but let's make sure
    
    // Click Start Tracking
    const startBtn = screen.getByRole('button', { name: /Start Tracking/i });
    fireEvent.click(startBtn);

    expect(mockOnSearch).toHaveBeenCalled();
    
    // Simulate parent component setting isSearching to true
    rerender(<ProductSearch {...defaultProps} isSearching={true} />);

    // Button should now be Stop Tracking
    expect(screen.getByRole('button', { name: /Stop Tracking/i })).toBeInTheDocument();
  });

  it('2. Change configuration (interval) -> button changes to Restart Tracking', async () => {
    const { rerender } = render(<ProductSearch {...defaultProps} />);
    
    const startBtn = screen.getByRole('button', { name: /Start Tracking/i });
    fireEvent.click(startBtn);

    // Now tracking is active
    rerender(<ProductSearch {...defaultProps} isSearching={true} />);

    // Change interval
    const selects = screen.getAllByRole('combobox');
    const intervalSelect = selects[selects.length - 1]; // scan interval
    fireEvent.change(intervalSelect, { target: { value: '30' } });

    // Should become Restart Tracking
    expect(await screen.findByRole('button', { name: /Restart Tracking/i })).toBeInTheDocument();
    
    // Original tracking should not have been cancelled (onCancel not called on dirty)
    expect(mockOnCancel).not.toHaveBeenCalled();
  });

  it('3. Multiple configuration changes -> only requires one restart', async () => {
    const { rerender } = render(<ProductSearch {...defaultProps} />);
    
    fireEvent.click(screen.getByRole('button', { name: /Start Tracking/i }));
    rerender(<ProductSearch {...defaultProps} isSearching={true} />);

    const selects = screen.getAllByRole('combobox');
    const intervalSelect = selects[selects.length - 1];
    
    fireEvent.change(intervalSelect, { target: { value: '30' } });
    fireEvent.change(intervalSelect, { target: { value: '60' } });
    
    expect(await screen.findByRole('button', { name: /Restart Tracking/i })).toBeInTheDocument();
    
    // Revert change
    fireEvent.change(intervalSelect, { target: { value: '15' } });
    
    // Should revert back to Stop Tracking!
    expect(await screen.findByRole('button', { name: /Stop Tracking/i })).toBeInTheDocument();
  });

  it('4. Restart Tracking clicks -> restarts tracker and reverts button', async () => {
    const { rerender } = render(<ProductSearch {...defaultProps} />);
    
    fireEvent.click(screen.getByRole('button', { name: /Start Tracking/i }));
    rerender(<ProductSearch {...defaultProps} isSearching={true} />);

    // Change interval to trigger Restart Tracking
    const selects = screen.getAllByRole('combobox');
    const intervalSelect = selects[selects.length - 1];
    fireEvent.change(intervalSelect, { target: { value: '30' } });

    const restartBtn = await screen.findByRole('button', { name: /Restart Tracking/i });
    
    // Need fake timers for setTimeout
    vi.useFakeTimers();
    
    fireEvent.click(restartBtn);
    
    // It should cancel the current tracking session cleanly
    expect(mockOnCancel).toHaveBeenCalled();
    
    // It hasn't started yet because of setTimeout
    const previousSearchCalls = mockOnSearch.mock.calls.length;
    
    vi.runAllTimers();
    
    // Now it should have started the new tracker
    expect(mockOnSearch.mock.calls.length).toBe(previousSearchCalls + 1);
    
    // Clean up timers
    vi.useRealTimers();
  });

  it('5. UI state change (search mode tab) -> button changes to Restart Tracking (because it changes what is searched)', async () => {
    const { rerender } = render(<ProductSearch {...defaultProps} />);
    
    fireEvent.click(screen.getByRole('button', { name: /Start Tracking/i }));
    rerender(<ProductSearch {...defaultProps} isSearching={true} />);

    // Change Search Mode
    const nearbyBtn = screen.getByRole('button', { name: /Nearby Area/i });
    fireEvent.click(nearbyBtn);

    expect(await screen.findByRole('button', { name: /Restart Tracking/i })).toBeInTheDocument();
  });
});
