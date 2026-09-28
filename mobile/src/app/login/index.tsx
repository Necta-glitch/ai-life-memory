import { useState } from 'react';
import { View, Text, Pressable, TextInput, StyleSheet, ActivityIndicator } from 'react-native';
import { router } from 'expo-router';
import {
  ArrowRight,
  Eye,
  EyeOff,
  Lock,
  Mail,
  Sparkles,
} from 'lucide-react-native';
import { setAuthenticated } from '@/lib/session';

type Mode = 'signin' | 'signup';

export default function Login() {
  const [mode, setMode] = useState<Mode>('signin');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const goHome = () => {
    setAuthenticated(true);
    router.replace('/');
  };

  const handleSubmit = () => {
    if (!email.trim() || !password.trim()) return;

    setLoading(true);
    setError('');

    setTimeout(() => {
      setLoading(false);
      goHome();
    }, 800);
  };

  const switchMode = () => {
    setMode((m) => (m === 'signin' ? 'signup' : 'signin'));
    setError('');
  };


  return (
    <View style={styles.screen}>
   

      <View style={styles.content}>
        <View style={styles.iconWrap}>
          <Sparkles size={28} strokeWidth={1.4} color="#a95c49" />
        </View>

        <Text style={styles.eyebrow}>
          {mode === 'signin' ? 'WELCOME BACK' : 'CREATE ACCOUNT'}
        </Text>

        <Text style={styles.title}>
          <Text>{mode === 'signin' ? 'Sign in to your ' : 'Begin your '}</Text>
          <Text style={styles.titleEm}>archive.</Text>
        </Text>

        <Text style={styles.subtitle}>
          {mode === 'signin'
            ? 'Your memories are waiting — quiet, private, and yours alone.'
            : 'A few seconds to create a private space for the things worth keeping.'}
        </Text>

        <View style={styles.form}>
          <View style={styles.field}>
            <Text style={styles.label}>EMAIL</Text>
            <View style={styles.inputWrap}>
              <Mail size={15} strokeWidth={1.7} color="#9c968f" />
              <TextInput
                style={styles.input}
                value={email}
                onChangeText={setEmail}
                placeholder="you@example.com"
                autoCapitalize="none"
                keyboardType="email-address"
                spellCheck={false}
              />
            </View>
          </View>

          <View style={styles.field}>
            <Text style={styles.label}>PASSWORD</Text>
            <View style={styles.inputWrap}>
              <Lock size={15} strokeWidth={1.7} color="#9c968f" />
              <TextInput
                style={styles.input}
                value={password}
                onChangeText={setPassword}
                placeholder="At least 6 characters"
                secureTextEntry={!showPassword}
                autoComplete={mode === 'signin' ? 'password' : 'new-password'}
                textContentType={mode === 'signin' ? 'password' : 'newPassword'}
              />
              <Pressable
                style={styles.eye}
                onPress={() => setShowPassword((s) => !s)}
                accessibilityLabel={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? (
                  <EyeOff size={15} strokeWidth={1.7} color="#9c968f" />
                ) : (
                  <Eye size={15} strokeWidth={1.7} color="#9c968f" />
                )}
              </Pressable>
            </View>
          </View>

          {error && <Text style={styles.error}>{error}</Text>}

          <Pressable
            style={[
              styles.submit,
              loading || !email.trim() || !password.trim() ? styles.submitDisabled : {},
            ]}
            onPress={handleSubmit}
            disabled={loading || !email.trim() || !password.trim()}
          >
            {loading ? (
              <ActivityIndicator size="small" color="#fffaf5" style={styles.spinner} />
            ) : (
              <>
                <Text style={styles.submitText}>
                  {mode === 'signin' ? 'Sign in' : 'Create account'}
                </Text>
                <ArrowRight size={16} color="#fffaf5" />
              </>
            )}
          </Pressable>
        </View>

        <View style={styles.switchRow}>
          <View style={styles.switchLine} />
          <Pressable style={styles.switch} onPress={switchMode}>
            <Text style={styles.switchText}>
              {mode === 'signin'
                ? "Don't have an account? Sign up"
                : 'Already have an account? Sign in'}
            </Text>
          </Pressable>
          <View style={styles.switchLine} />
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    backgroundColor: '#f6f3ed',
  },
  top: {
    paddingHorizontal: 22,
    height: 48,
    display: 'flex',
    alignItems: 'flex-end',
    justifyContent: 'center',
  },
  back: {
    display: 'flex',
    alignItems: 'center',
    gap: 5,
    borderWidth: 0,
    backgroundColor: 'transparent',
  },
  backText: {
    color: '#9e978f',
    fontFamily: 'DM Mono',
    fontSize: 9,
    letterSpacing: 0.1,
    textTransform: 'uppercase',
  },
  content: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 32,
    textAlign: 'center',
  },
  iconWrap: {
    width: 72,
    height: 72,
    borderRadius: 36,
    borderWidth: 1,
    borderColor: '#ddd6cc',
    backgroundColor: '#efebe4',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 28,
  },
  eyebrow: {
    fontFamily: 'DM Mono',
    fontSize: 9,
    letterSpacing: 1.62,
    color: '#a95c49',
    fontWeight: '500',
    marginBottom: 14,
  },
  title: {
    marginBottom: 16,
    fontFamily: 'Libre Baskerville',
    fontSize: 30,
    fontWeight: '400',
    lineHeight: 35.4,
    letterSpacing: -1.2,
    color: '#292725',
    maxWidth: 300,
  },
  titleEm: {
    fontStyle: 'italic',
    color: '#a95c49',
  },
  subtitle: {
    marginBottom: 32,
    fontSize: 13,
    lineHeight: 20.15,
    color: '#858079',
    maxWidth: 280,
  },
  form: {
    width: '100%',
    maxWidth: 320,
    gap: 16,
  },
  field: {},
  label: {
    marginBottom: 7,
    color: '#8b837a',
    fontFamily: 'DM Mono',
    fontSize: 9,
    letterSpacing: 0.9,
    textTransform: 'uppercase',
  },
  inputWrap: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    paddingHorizontal: 13,
    height: 46,
    backgroundColor: '#eeebe4',
    borderWidth: 1,
    borderColor: '#dad2c8',
    borderRadius: 10,
  },
  input: {
    flex: 1,
    color: '#2d2b29',
    fontSize: 13,
    fontFamily: 'DM Sans',
  },
  eye: {
    padding: 4,
    justifyContent: 'center',
    alignItems: 'center',
  },
  error: {
    marginTop: 8,
    paddingHorizontal: 13,
    paddingVertical: 10,
    borderRadius: 8,
    backgroundColor: '#f5e4e0',
    borderLeftWidth: 2,
    borderLeftColor: '#c4624f',
    color: '#8f3f33',
    fontSize: 11,
    lineHeight: 15.95,
    textAlign: 'left',
  },
  submit: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 9,
    width: '100%',
    paddingVertical: 14,
    borderRadius: 10,
    backgroundColor: '#a95c49',
    marginTop: 4,
  },
  submitDisabled: {
    opacity: 0.45,
  },
  submitText: {
    color: '#fffaf5',
    fontSize: 12,
    fontWeight: '600',
    letterSpacing: 0.24,
  },
  spinner: {
    marginTop: 1,
  },
  switchRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 14,
    marginTop: 28,
    width: '100%',
    maxWidth: 320,
  },
  switchLine: {
    flex: 1,
    height: 1,
    backgroundColor: '#dbd5cc',
  },
  switch: {
    borderWidth: 0,
    backgroundColor: 'transparent',
  },
  switchText: {
    color: '#858079',
    fontSize: 11,
    fontFamily: 'DM Sans',
  },
});

export { Login };