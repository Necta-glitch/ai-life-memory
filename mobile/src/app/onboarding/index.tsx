import { View, Text, Pressable, StyleSheet } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useRouter } from 'expo-router';
import {
  ArrowRight,
  Bookmark,
  Headphones,
  PenLine,
  Sparkles,
  X,
  type LucideIcon,
} from 'lucide-react-native';
import { useState, type ReactNode } from 'react';
import { STORAGE_KEYS } from '@/constants/storage';

type Slide = {
  eyebrow: string;
  icon: LucideIcon;
  title: ReactNode;
  body: string;
  detail: string;
  featureIcon: LucideIcon;
  featureLabel: string;
};

const slides: Slide[] = [
  {
    eyebrow: 'WELCOME',
    icon: Sparkles,
    title: 'A life, remembered',
    body: 'Memory is a quiet, private archive for the moments that shape your days.',
    detail: 'No feeds. No followers. No noise. Just you and the things worth keeping.',
    featureIcon: PenLine,
    featureLabel: 'Write freely',
  },
  {
    eyebrow: 'CAPTURE',
    icon: PenLine,
    title: 'Write it down, before it fades',
    body: 'Jot a note, record a voice memo, or simply give a moment a name.',
    detail: 'Every entry becomes part of your timeline — a living record of your life.',
    featureIcon: Sparkles,
    featureLabel: 'AI summaries',
  },
  {
    eyebrow: 'UNDERSTOOD',
    icon: Bookmark,
    title: 'Memory understands',
    body: 'Each entry is gently read and distilled into a short, clear summary.',
    detail: 'So you can search your past the way you think — by feeling, not just keywords.',
    featureIcon: Sparkles,
    featureLabel: 'Smart search',
  },
  {
    eyebrow: 'TIMELINE',
    icon: Headphones,
    title: 'Your story, in order',
    body: 'Memories appear chronologically, like chapters in a beautifully bound book.',
    detail: 'Scroll back through months and years. Find patterns. Watch your life unfold.',
    featureIcon: PenLine,
    featureLabel: 'Chronological',
  },
];

export default function Onboarding() {
  const router = useRouter();
  const [current, setCurrent] = useState(0);
  const isLast = current === slides.length - 1;

  const goToLogin = async () => {
    await AsyncStorage.setItem(STORAGE_KEYS.ONBOARDING_COMPLETED, 'true');
    router.replace('/login');
  };

  const next = async () => {
    if (isLast) {
      await goToLogin();
    } else {
      setCurrent((c) => c + 1);
    }
  };

  const skip = () => goToLogin();

  const slide = slides[current];
  const Icon = slide.icon;
  const FeatureIcon = slide.featureIcon;

  return (
    <View style={styles.screen}>
      <View style={styles.top}>
        <View style={styles.brand}>
          <View style={styles.mark}>
            <Sparkles size={14} color="#f6f3ed" strokeWidth={1.8} />
          </View>
          <Text style={styles.brandText}>MEMORY</Text>
        </View>
        <Pressable style={styles.skip} onPress={skip}>
          <Text style={styles.skipText}>Skip</Text>
          <X size={14} color="#9e978f" />
        </Pressable>
      </View>

      <View style={styles.content}>
        <View style={styles.iconWrap}>
          <Icon size={28} color="#a95c49" strokeWidth={1.4} />
        </View>

        <Text style={styles.eyebrow}>{slide.eyebrow}</Text>
        <Text style={styles.title}>{slide.title}</Text>
        <Text style={styles.body}>{slide.body}</Text>

        <View style={styles.detail}>
          <View style={styles.detailLine} />
          <Text style={styles.detailText}>{slide.detail}</Text>
        </View>

        <View style={styles.features}>
          <View style={styles.feature}>
            <FeatureIcon size={16} color="#a95c49" strokeWidth={1.5} />
            <Text style={styles.featureText}>{slide.featureLabel}</Text>
          </View>
        </View>
      </View>

      <View style={styles.bottom}>
        <View style={styles.dots}>
          {slides.map((_, i) => (
            <Pressable
              key={i}
              style={[styles.dot, i === current && styles.dotActive]}
              onPress={() => setCurrent(i)}
              accessibilityRole="button"
              accessibilityLabel={`Go to slide ${i + 1}`}
            />
          ))}
        </View>

        <Pressable style={styles.next} onPress={next}>
          <Text style={styles.nextText}>{isLast ? 'Begin' : 'Continue'}</Text>
          <ArrowRight size={16} color="#fffaf5" />
        </Pressable>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    flexDirection: 'column',
    backgroundColor: '#f6f3ed',
  },
  top: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 22,
    height: 48,
  },
  brand: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  brandText: {
    fontFamily: 'DM Mono',
    fontSize: 11,
    fontWeight: '500',
    letterSpacing: 2.3,
    color: '#2d2b29',
  },
  mark: {
    width: 22,
    height: 22,
    borderRadius: 7,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#a95c49',
  },
  skip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
  },
  skipText: {
    color: '#9e978f',
    fontFamily: 'DM Mono',
    fontSize: 9,
    letterSpacing: 1,
    textTransform: 'uppercase',
  },
  content: {
    flex: 1,
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 32,
  },
  iconWrap: {
    width: 72,
    height: 72,
    borderRadius: 36,
    borderWidth: 1,
    borderColor: '#ddd6cc',
    backgroundColor: '#efebe4',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 28,
  },
  eyebrow: {
    fontFamily: 'DM Mono',
    fontSize: 9,
    letterSpacing: 1.6,
    color: '#a95c49',
    fontWeight: '500',
    marginBottom: 14,
  },
  title: {
    marginBottom: 16,
    fontFamily: 'Libre Baskerville',
    fontSize: 32,
    fontWeight: '400',
    lineHeight: 38,
    letterSpacing: -1.3,
    color: '#292725',
    maxWidth: 300,
    textAlign: 'center',
  },
  body: {
    marginBottom: 24,
    fontSize: 14,
    lineHeight: 22,
    color: '#69645e',
    maxWidth: 290,
    textAlign: 'center',
  },
  detail: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
    maxWidth: 290,
  },
  detailLine: {
    width: 1,
    flexShrink: 0,
    alignSelf: 'stretch',
    backgroundColor: '#c48672',
    minHeight: 32,
    marginTop: 2,
  },
  detailText: {
    flex: 1,
    fontFamily: 'Libre Baskerville',
    fontStyle: 'italic',
    fontSize: 12,
    lineHeight: 18,
    color: '#8a847d',
  },
  features: {
    flexDirection: 'row',
    gap: 10,
    marginTop: 36,
    flexWrap: 'wrap',
    justifyContent: 'center',
  },
  feature: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingVertical: 7,
    paddingHorizontal: 11,
    borderWidth: 1,
    borderColor: 'rgba(45,43,41,0.1)',
    borderRadius: 999,
    backgroundColor: '#eeebe4',
  },
  featureText: {
    fontFamily: 'DM Mono',
    fontSize: 8,
    letterSpacing: 0.6,
    color: '#716b64',
  },
  bottom: {
    paddingHorizontal: 22,
    paddingBottom: 30,
    flexDirection: 'column',
    alignItems: 'center',
    gap: 22,
  },
  dots: {
    flexDirection: 'row',
    gap: 7,
  },
  dot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#d3cdc4',
  },
  dotActive: {
    width: 18,
    borderRadius: 999,
    backgroundColor: '#a95c49',
  },
  next: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 9,
    width: '100%',
    justifyContent: 'center',
    paddingVertical: 14,
    borderRadius: 10,
    backgroundColor: '#a95c49',
  },
  nextText: {
    color: '#fffaf5',
    fontSize: 12,
    fontWeight: '600',
    letterSpacing: 0.2,
  },
});
