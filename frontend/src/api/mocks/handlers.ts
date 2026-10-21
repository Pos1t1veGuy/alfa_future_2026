import { delay, http, HttpResponse } from 'msw'
import { demoApplications } from '../../mock/demo'
import { products } from '../../mock/products'

export const handlers = [
  http.get('/api/v1/products/', async () => { await delay(350); return HttpResponse.json(products) }),
  http.get('/api/v1/applications/', async () => { await delay(450); return HttpResponse.json({ count: demoApplications.length, results: demoApplications }) }),
  http.get('/api/v1/bank/applications/', async () => { await delay(450); return HttpResponse.json({ count: demoApplications.length, results: demoApplications }) }),
  http.get('/api/v1/applications/:id/', ({ params }) => HttpResponse.json(demoApplications.find((item) => item.id === params.id) ?? {}, { status: demoApplications.some((item) => item.id === params.id) ? 200 : 404 })),
  http.post('/api/v1/documents/:id/ocr/', async () => { await delay(600); return HttpResponse.json({ fields: { inn: '7704123456', revenue: 1500000 }, confidence: 0.94 }) }),
]
