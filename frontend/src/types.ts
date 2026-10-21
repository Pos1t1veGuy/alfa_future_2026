export type ApplicationStatus =
  | 'draft'
  | 'submitted'
  | 'review'
  | 'additional_info'
  | 'approved'
  | 'declined'

export type Product = {
  id: string
  name: string
  description: string
  rate: string
  maxAmount: number
  term: string
  icon: string
}

export type LoanApplication = {
  id: string
  productId: string
  amount: number
  termMonths: number
  purpose: string
  status: ApplicationStatus
  createdAt: string
}
