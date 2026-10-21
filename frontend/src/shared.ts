export const money = (value: number) => new Intl.NumberFormat('ru-RU').format(value) + ' ₽'
export const date = (value: string) => new Intl.DateTimeFormat('ru-RU', { day: '2-digit', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit' }).format(new Date(value))
