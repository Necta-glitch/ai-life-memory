import { useEffect, useState } from 'react';
import { View, StyleSheet, ActivityIndicator } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useRouter } from 'expo-router';
import { STORAGE_KEYS } from '@/constants/storage';
import { isAuthenticated } from '@/lib/session';

/**
 * App entry gate.
 *
 * Flow: Onboarding (once) → Login → Main App (tabs)
 */
export default function HomeScreen() {
  const router = useRouter();
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    const gate = async () => {
      const onboardingDone = await AsyncStorage.getItem(STORAGE_KEYS.ONBOARDING_COMPLETED);

      if (onboardingDone !== 'true') {
        router.replace('/onboarding');
        return;
      }

      // Onboarding done, check auth
      if (!isAuthenticated()) {
        router.replace('/login');
        return;
      }

      // Authenticated, go to tabs
      router.replace('/(tabs)' as any);
    };

    gate().finally(() => setChecking(false));
  }, [router]);

  if (checking) {
    return (
      <View style={styles.loading}>
        <ActivityIndicator size="large" color="#a95c49" />
      </View>
    );
  }

  return null;
}

const styles = StyleSheet.create({
  loading: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#f6f3ed',
  },
});