import { useParams } from 'react-router-dom';
import { PageHeader } from '@/components/common/PageHeader';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { useApiQuery } from '@/hooks/useApiQuery';
import { getCustomer } from '@/api/customers';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export default function CustomerDetail() {
  const { customerId } = useParams<{ customerId: string }>();
  const { data, isLoading, error } = useApiQuery(() => getCustomer(Number(customerId)), [customerId]);

  if (isLoading) return <LoadingSpinner />;
  if (error || !data) return <p className="text-red-600">Failed to load customer</p>;

  return (
    <div>
      <PageHeader title={data.name} description={`Code: ${data.customer_code}`} />
      <div className="grid grid-cols-2 gap-4">
        <Card>
          <CardHeader className="py-3 px-4"><CardTitle className="text-sm">Contact Info</CardTitle></CardHeader>
          <CardContent className="px-4 pb-3 space-y-1 text-sm">
            <p><span className="text-muted-foreground">Contact:</span> {data.contact_person || '-'}</p>
            <p><span className="text-muted-foreground">Email:</span> {data.email || '-'}</p>
            <p><span className="text-muted-foreground">Phone:</span> {data.phone || '-'}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="py-3 px-4"><CardTitle className="text-sm">Address</CardTitle></CardHeader>
          <CardContent className="px-4 pb-3 space-y-1 text-sm">
            <p>{data.address_line1 || '-'}</p>
            {data.address_line2 && <p>{data.address_line2}</p>}
            <p>{[data.city, data.state, data.postal_code].filter(Boolean).join(', ') || '-'}</p>
            <p>{data.country}</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
