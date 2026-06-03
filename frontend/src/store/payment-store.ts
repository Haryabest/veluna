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
  credits: number;
  totalSpent: number;
  totalEarned: number;
  transactions: Transaction[];
  setBalance: (gems: number, credits: number, spent?: number, earned?: number) => void;
  setTransactions: (transactions: Transaction[]) => void;
}

export const usePaymentStore = create<PaymentState>((set) => ({
  gems: 0,
  credits: 0,
  totalSpent: 0,
  totalEarned: 0,
  transactions: [],
  setBalance: (gems, credits, spent = 0, earned = 0) =>
    set({ gems, credits, totalSpent: spent, totalEarned: earned }),
  setTransactions: (transactions) => set({ transactions }),
}));
