import { useState, useCallback } from 'react';
import { getActiveAccountFromStorage, setActiveAccountInStorage } from '../services/api';

type AccountId = 'car-j-works' | 'car-j-home';

/**
 * Custom hook that manages the active account state.
 * Keeps localStorage and the Axios interceptor in sync with React state.
 */
export function useActiveAccount() {
  const [activeAccount, setActiveAccountState] = useState<AccountId>(
    () => getActiveAccountFromStorage() as AccountId
  );

  const switchAccount = useCallback((id: AccountId) => {
    setActiveAccountInStorage(id);
    setActiveAccountState(id);
  }, []);

  return { activeAccount, switchAccount };
}
