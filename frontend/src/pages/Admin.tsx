import { lazy, Suspense } from 'react';
import { PageHeader } from '@/components/common/PageHeader';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

const AdminSystem = lazy(() =>
  import('@/components/admin/AdminSystem').then((m) => ({ default: m.AdminSystem }))
);
const AdminCustomers = lazy(() =>
  import('@/components/admin/AdminCustomers').then((m) => ({ default: m.AdminCustomers }))
);
const AdminWorkOrders = lazy(() =>
  import('@/components/admin/AdminWorkOrders').then((m) => ({ default: m.AdminWorkOrders }))
);
const AdminBatteryProfiles = lazy(() =>
  import('@/components/admin/AdminBatteryProfiles').then((m) => ({
    default: m.AdminBatteryProfiles,
  }))
);
const AdminTechPubs = lazy(() =>
  import('@/components/admin/AdminTechPubs').then((m) => ({ default: m.AdminTechPubs }))
);
const AdminTools = lazy(() =>
  import('@/components/admin/AdminTools').then((m) => ({ default: m.AdminTools }))
);
const AdminCalibration = lazy(() =>
  import('@/components/admin/AdminCalibration').then((m) => ({ default: m.AdminCalibration }))
);

function TabFallback() {
  return <LoadingSpinner text="Loading..." />;
}

export default function Admin() {
  return (
    <div>
      <PageHeader title="Admin" description="System management and configuration" />
      <Tabs defaultValue="system">
        <TabsList variant="line" className="mb-4">
          <TabsTrigger value="system">System</TabsTrigger>
          <TabsTrigger value="customers">Customers</TabsTrigger>
          <TabsTrigger value="work-orders">Work Orders</TabsTrigger>
          <TabsTrigger value="battery-profiles">Battery Profiles</TabsTrigger>
          <TabsTrigger value="tech-pubs">Tech Pubs</TabsTrigger>
          <TabsTrigger value="tools">Tools</TabsTrigger>
          <TabsTrigger value="calibration">Calibration</TabsTrigger>
        </TabsList>

        <TabsContent value="system">
          <Suspense fallback={<TabFallback />}>
            <AdminSystem />
          </Suspense>
        </TabsContent>

        <TabsContent value="customers">
          <Suspense fallback={<TabFallback />}>
            <AdminCustomers />
          </Suspense>
        </TabsContent>

        <TabsContent value="work-orders">
          <Suspense fallback={<TabFallback />}>
            <AdminWorkOrders />
          </Suspense>
        </TabsContent>

        <TabsContent value="battery-profiles">
          <Suspense fallback={<TabFallback />}>
            <AdminBatteryProfiles />
          </Suspense>
        </TabsContent>

        <TabsContent value="tech-pubs">
          <Suspense fallback={<TabFallback />}>
            <AdminTechPubs />
          </Suspense>
        </TabsContent>

        <TabsContent value="tools">
          <Suspense fallback={<TabFallback />}>
            <AdminTools />
          </Suspense>
        </TabsContent>

        <TabsContent value="calibration">
          <Suspense fallback={<TabFallback />}>
            <AdminCalibration />
          </Suspense>
        </TabsContent>
      </Tabs>
    </div>
  );
}
