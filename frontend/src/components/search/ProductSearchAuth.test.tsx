import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import ProductSearch from './ProductSearch';
import { useAuthStore } from '../../store/authStore';

// Mock live console store
vi.mock('../../store/liveConsoleStore', async (importOriginal) => {
  const actual = await importOriginal<any>();
  return {
    ...actual,
    liveConsoleStore: {
      clearLogs: vi.fn(),
      setScanState: vi.fn(),
    }
  };
});

// We can mock the modal since its behavior is handled globally, but to test the
// actual "execute action on unlock" we just trigger the store's executePendingAction.
describe('ProductSearch Authentication Flow', () => {
  let onSearchMock: any;
  let onCancelMock: any;

  beforeEach(() => {
    // Mock localStorage
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

    onSearchMock = vi.fn();
    onCancelMock = vi.fn();
    
    // Reset store to locked state
    useAuthStore.setState({ 
      isLocked: true, 
      securityEnabled: true, 
      showModal: false, 
      pendingAction: null 
    });
  });

  it('1. Locked -> Start Tracking -> requires auth -> executePendingAction -> tracking starts', async () => {
    render(
      <ProductSearch
        onSearch={onSearchMock}
        isSearching={false}
        onCancel={onCancelMock}
        compact={false}
        initialConfig={{ platforms: ["swiggy"] }}
      />
    );

    const startBtn = screen.getByText('Start Tracking');
    fireEvent.click(startBtn);

    // It should NOT call onSearch yet
    expect(onSearchMock).not.toHaveBeenCalled();
    // Modal should be shown
    expect(useAuthStore.getState().showModal).toBe(true);
    expect(useAuthStore.getState().pendingAction).toBeTruthy();

    // Simulate successful unlock
    useAuthStore.getState().executePendingAction();

    // Now it should be called
    expect(onSearchMock).toHaveBeenCalled();
  });

  it('2. Locked -> Stop Tracking -> requires auth -> executePendingAction -> tracking stops', async () => {
    render(
      <ProductSearch
        onSearch={onSearchMock}
        isSearching={true} // tracking is active
        onCancel={onCancelMock}
        compact={false}
        initialConfig={{ platforms: ["swiggy"] }}
      />
    );

    const stopBtn = screen.getByText('Stop Tracking');
    fireEvent.click(stopBtn);

    expect(onCancelMock).not.toHaveBeenCalled();
    expect(useAuthStore.getState().showModal).toBe(true);

    useAuthStore.getState().executePendingAction();

    expect(onCancelMock).toHaveBeenCalled();
  });

  it('4. Locked -> change interval -> requires auth -> executePendingAction -> interval changes', async () => {
    render(
      <ProductSearch
        onSearch={onSearchMock}
        isSearching={false}
        onCancel={onCancelMock}
        compact={false}
        initialConfig={{ platforms: ["swiggy"], run_interval_minutes: 15 }}
      />
    );

    // Find the interval select
    const select = screen.getByDisplayValue('Every 15 mins');
    
    fireEvent.change(select, { target: { value: '30' } });

    // The value should remain 15 because the onChange is intercepted by requestAuth
    expect((select as HTMLSelectElement).value).toBe('15');
    
    expect(useAuthStore.getState().showModal).toBe(true);
    
    useAuthStore.getState().executePendingAction();
    
    // Now it should be updated
    await waitFor(() => {
      expect((select as HTMLSelectElement).value).toBe('30');
    });
  });

  it('9. Cancel password modal -> no action occurs', async () => {
    render(
      <ProductSearch
        onSearch={onSearchMock}
        isSearching={false}
        onCancel={onCancelMock}
        compact={false}
        initialConfig={{ platforms: ["swiggy"] }}
      />
    );

    const startBtn = screen.getByText('Start Tracking');
    fireEvent.click(startBtn);

    expect(onSearchMock).not.toHaveBeenCalled();
    
    // User cancels the modal
    useAuthStore.getState().clearPendingAction();
    useAuthStore.getState().setShowModal(false);

    // Still not called
    expect(onSearchMock).not.toHaveBeenCalled();
  });

  it('12. Already unlocked -> protected actions work normally without unnecessary password prompts', async () => {
    // Unlocked!
    useAuthStore.setState({ isLocked: false, securityEnabled: true });

    render(
      <ProductSearch
        onSearch={onSearchMock}
        isSearching={false}
        onCancel={onCancelMock}
        compact={false}
        initialConfig={{ platforms: ["swiggy"] }}
      />
    );

    const startBtn = screen.getByText('Start Tracking');
    fireEvent.click(startBtn);

    // Should immediately call
    expect(onSearchMock).toHaveBeenCalled();
    expect(useAuthStore.getState().showModal).toBe(false);
  });
});
