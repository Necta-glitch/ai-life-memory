import React from 'react';
import { View, StyleSheet, Pressable } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Clock3, Bookmark } from 'lucide-react-native';
import type { BottomTabBarProps } from 'expo-router/build/react-navigation/bottom-tabs/types';

type TabConfig = {
  name: string;
  label: string;
  icon: React.ComponentType<{ size?: number; strokeWidth?: number; color?: string }>;
};

const TABS: TabConfig[] = [
  { name: '(tabs)/index', label: 'Memory', icon: Clock3 },
  { name: '(tabs)/saved', label: 'Saved', icon: Bookmark },
];

export default function CustomTabBar(props: BottomTabBarProps) {
  const { state, navigation, insets } = props;
  const safeInsets = useSafeAreaInsets();

  const focusedRoute = state.routes[state.index];
  const activeColor = '#a95c49';
  const inactiveColor = '#a19a91';

  return (
    <View
      style={[
        styles.container,
        {
          paddingBottom: Math.max(insets.bottom, safeInsets.bottom),
        },
      ]}
      pointerEvents="box-none"
    >
      <View
        style={styles.dock}
        pointerEvents="auto"
      >
        {TABS.map((tab) => {
          const isActive = focusedRoute?.name === tab.name;
          const Icon = tab.icon;

          const handlePress = () => {
            navigation.navigate(tab.name as never);
          };

          return (
            <Pressable
              key={tab.name}
              onPress={handlePress}
              accessibilityLabel={tab.label}
              accessibilityRole="button"
              accessibilityState={{ selected: isActive }}
              style={({ pressed }) => [
                styles.tabItem,
                {
                  backgroundColor: isActive
                    ? activeColor
                    : pressed
                    ? 'rgba(45,43,41,0.05)'
                    : 'transparent',
                  transform: [{ scale: pressed ? 0.95 : 1 }],
                },
              ]}
              android_ripple={{ color: activeColor, borderless: true }}
            >
              <Icon
                size={22}
                strokeWidth={isActive ? 2.5 : 2}
                color={isActive ? '#fffaf5' : inactiveColor}
              />
            </Pressable>
          );
        })}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    flexDirection: 'column',
    alignItems: 'center',
    paddingVertical: 10,
    pointerEvents: 'none',
    zIndex: 100,
  },
  dock: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderWidth: 1,
    borderColor: 'rgba(45,43,41,0.1)',
    borderRadius: 999,
    backgroundColor: 'rgba(250,248,243,0.92)',
    shadowColor: 'rgba(57,48,39,0.14)',
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 1,
    shadowRadius: 30,
    elevation: 8,
  },
  tabItem: {
    width: 48,
    height: 48,
    borderRadius: 24,
    alignItems: 'center',
    justifyContent: 'center',
  },
});