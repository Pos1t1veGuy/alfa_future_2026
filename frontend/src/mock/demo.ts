import type { ApplicationStatus, LoanApplication, Product } from '../types'

export type Role = 'client' | 'bank_manager' | 'admin'
export type User = { id: string; name: string; company: string; role: Role; email: string }
export type HistoryItem = { id: string; status: ApplicationStatus; date: string; author: string; comment: string }
export type DemoApplication = LoanApplication & {
  client: string; company: string; rate?: number; manager?: string; history: HistoryItem[]; unread?: boolean
}

export const demoUsers: Record<Role, User> = {
  client: { id: 'usr-1', name: 'Ирина Соколова', company: 'ООО «Вектор»', role: 'client', email: 'i.sokolova@vector.ru' },
  bank_manager: { id: 'usr-2', name: 'Алексей Смирнов', company: 'Альфа-Банк', role: 'bank_manager', email: 'a.smirnov@alfabank.ru' },
  admin: { id: 'usr-3', name: 'Мария Ким', company: 'Альфа-Банк', role: 'admin', email: 'm.kim@alfabank.ru' },
}

export const demoApplications: DemoApplication[] = [
  { id: 'CR-482901', productId: 'turnover', amount: 2500000, termMonths: 24, purpose: 'Закупка сезонного товара', status: 'review', createdAt: '2026-10-18T08:30:00Z', client: 'Ирина Соколова', company: 'ООО «Вектор»', manager: 'Алексей Смирнов', unread: true, history: [
    { id: 'h1', status: 'submitted', date: '2026-10-18T08:30:00Z', author: 'Ирина Соколова', comment: 'Заявка отправлена в банк' },
    { id: 'h2', status: 'review', date: '2026-10-18T08:32:00Z', author: 'Кредитный конвейер', comment: 'Проводим автоматические проверки и оценку заявки' },
  ] },
  { id: 'CR-482744', productId: 'equipment', amount: 4800000, termMonths: 36, purpose: 'Покупка производственной линии', status: 'additional_info', createdAt: '2026-10-16T10:15:00Z', client: 'Ирина Соколова', company: 'ООО «Вектор»', manager: 'Алексей Смирнов', unread: true, history: [
    { id: 'h3', status: 'submitted', date: '2026-10-16T10:15:00Z', author: 'Ирина Соколова', comment: 'Заявка отправлена в банк' },
    { id: 'h4', status: 'additional_info', date: '2026-10-17T12:00:00Z', author: 'Алексей Смирнов', comment: 'Нужна выписка по расчётному счёту за последние 3 месяца' },
  ] },
  { id: 'CR-482612', productId: 'universal', amount: 800000, termMonths: 12, purpose: 'Пополнение оборотных средств', status: 'approved', createdAt: '2026-10-12T09:00:00Z', client: 'Павел Орлов', company: 'ИП Орлов П. А.', manager: 'Алексей Смирнов', rate: 19.5, history: [
    { id: 'h5', status: 'submitted', date: '2026-10-12T09:00:00Z', author: 'Павел Орлов', comment: 'Заявка отправлена в банк' },
    { id: 'h6', status: 'approved', date: '2026-10-13T15:05:00Z', author: 'Алексей Смирнов', comment: 'Одобрено на запрошенных условиях' },
  ] },
]

export const statusText: Record<ApplicationStatus, string> = {
  draft: 'Черновик', submitted: 'Заявка принята', review: 'Рассматривается', additional_info: 'Нужны уточнения', approved: 'Одобрено', declined: 'Не одобрено',
}

export const clientStatusText: Record<ApplicationStatus, string> = {
  draft: 'Заполните заявку, чтобы отправить её в банк', submitted: 'Заявка принята и поступила в банк', review: 'Проверяем данные компании и готовим решение', additional_info: 'Нам понадобилась дополнительная информация', approved: 'Поздравляем, кредит одобрен', declined: 'По этой заявке сейчас не можем предложить кредит',
}

export const productById = (products: Product[], id: string) => products.find((product) => product.id === id)
