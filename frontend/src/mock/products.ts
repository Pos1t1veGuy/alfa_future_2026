import type { Product } from '../types'

export const products: Product[] = [
  {
    id: 'turnover',
    name: 'На пополнение оборотных средств',
    description: 'Закупайте товар, оплачивайте аренду и закрывайте кассовые разрывы.',
    rate: 'от 18,5%',
    maxAmount: 10000000,
    term: 'до 36 месяцев',
    icon: '↻',
  },
  {
    id: 'equipment',
    name: 'На оборудование',
    description: 'Обновляйте технику и развивайте производство без изъятия всей суммы из оборота.',
    rate: 'от 17,9%',
    maxAmount: 15000000,
    term: 'до 60 месяцев',
    icon: '⌘',
  },
  {
    id: 'universal',
    name: 'Универсальный кредит',
    description: 'Для задач бизнеса, когда нужна свободная цель финансирования.',
    rate: 'от 19,5%',
    maxAmount: 5000000,
    term: 'до 24 месяцев',
    icon: '◈',
  },
]

export const statusLabels = {
  draft: 'Черновик',
  submitted: 'Заявка отправлена',
  review: 'Банк рассматривает заявку',
  additional_info: 'Нужны уточнения',
  approved: 'Одобрено',
  declined: 'Не одобрено',
} as const

export const statusSteps = [
  { id: 'submitted', title: 'Заявка принята', description: 'Мы получили вашу заявку' },
  { id: 'review', title: 'Проверяем данные', description: 'Проводим оценку компании' },
  { id: 'approved', title: 'Решение готово', description: 'Сообщим о результате здесь' },
]
