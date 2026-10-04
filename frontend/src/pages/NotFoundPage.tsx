import { Compass } from 'lucide-react'
import { PageContainer } from '../components/layout/Page'
import { ButtonLink } from '../components/ui/Button'
import { EmptyState } from '../components/ui/Feedback'
import { useDocumentTitle } from '../hooks/useDocumentTitle'

export function NotFoundPage() {
  useDocumentTitle('Page not found')
  return (
    <PageContainer className="py-20">
      <EmptyState
        icon={<Compass className="h-6 w-6" aria-hidden />}
        title="We couldn't find that page"
        description="The link may be broken or the page may have moved."
        action={<ButtonLink to="/">Go to homepage</ButtonLink>}
      />
    </PageContainer>
  )
}
