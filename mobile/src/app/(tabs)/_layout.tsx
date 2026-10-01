import { Tabs } from 'expo-router';
import { MemoriesProvider } from '@/context/MemoriesContext';
import CustomTabBar from '@/components/TabBar';

export default function TabsLayout() {
  return (
    <MemoriesProvider>
      <Tabs
        screenOptions={{
          headerShown: false,
        }}
        tabBar={(props) => <CustomTabBar {...props} />}
      >
        <Tabs.Screen name="index" options={{ title: 'Memory' }} />
        <Tabs.Screen name="saved" options={{ title: 'Saved' }} />
      </Tabs>
    </MemoriesProvider>
  );
}