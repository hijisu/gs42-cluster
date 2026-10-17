import { useQuery } from '@tanstack/react-query'
import { fetchStaffReservations } from '../staff-room/api'

/** 키가 ['staff','reservations',…]라 예약 승인·반려 때 함께 새로고침된다. */
export const useReservationsByStatus = (status: 'pending' | 'approved', date?: string) =>
  useQuery({
    queryKey: ['staff', 'reservations', 'home', status, date ?? 'all'],
    queryFn: () => fetchStaffReservations(date ?? '', status),
  })
