import { useEffect, useState } from 'react';
import { View, StyleSheet, ActivityIndicator } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useRouter } from 'expo-router';
import { STORAGE_KEYS } from '@/constants/storage';

/**
 * App entry gate.
 *
 * Flow: Onboarding (once) → Main App (tabs)
 */
export default function HomeScreen() {
  const router = useRouter();
  const [ready] = useState(false);

  useEffect(() => {
    const gate = async () => {
      const onboardingDone = await AsyncStorage.getItem(STORAGE_KEYS.ONBOARDING_COMPLETED);
      if (onboardingDone !== 'true') {
        router.replace('/onboarding');
        return;
      }

      // Onboarding done, go to tabs
      router.replace('/(tabs)' as any);
    };

    gate();
  }, [router]);

  if (!ready) {
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