
import api from '../js/api'

export const fetchLotsSummary = () => api.get('/admin/lots')
export const fetchLotDetails = (lotId, params={}) => api.post('/admin/reports', { view: 'reservations', lot_id: lotId, ...params })
export const fetchOccupancy = () => api.post('/admin/reports', { view: 'occupancy' })
export const fetchRevenue = (month, year) => api.post('/admin/reports', { view: 'revenue', month, year })
export const fetchReservationsByLot = () => api.post('/admin/reports', { view: 'reservations_by_lot' })
export const searchAll = (type, search_by, value) => api.get('/admin/search', { params: { type, search_by, value } })
