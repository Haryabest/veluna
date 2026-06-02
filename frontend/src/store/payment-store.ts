import { create } from "zustand";

export interface Transaction {
  id: string;
  type: string;
  amount: number;
  balance_after: number;
  description: string;
  created_at: string;
}

interface PaymentState {
  gems: number;
  totalSpent: number;
  totalEarned: number;
  transactions: Transaction[];
  setBalance: (gems: number, spent: number, earned: number) => void;
  setTransactions: (transactions: Transaction[]) => void;
}

export const usePaymentStore = create<PaymentState>((set) => ({
  gems: 0,
  totalSpent: 0,
  totalEarned: 0,
  transactions: [],
  setBalance: (gems, spent, earned) => set({ gems, totalSpent: spent, totalEarned: earned }),
  setTransactions: (transactions) => set({ transactions }),
}));
