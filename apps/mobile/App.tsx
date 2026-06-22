import AsyncStorage from "@react-native-async-storage/async-storage";
import { StatusBar } from "expo-status-bar";
import * as Notifications from "expo-notifications";
import React, { useEffect, useMemo, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View
} from "react-native";
import { Bell, CalendarDays, Check, MapPin, MessageCircle, MoonStar, Search, Sparkles, Trash2 } from "lucide-react-native";

const API_BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL ?? (Platform.OS === "android" ? "http://10.0.2.2:8000" : "http://127.0.0.1:8000");
const PROFILE_KEY = "trustastro.profile";

type BirthProfile = {
  birthDate: string;
  birthTime: string;
  birthTimeConfidence: "exact" | "approximate" | "unknown";
  birthplaceText: string;
  latitude: number;
  longitude: number;
  timezone: string;
  language: string;
  consent: {
    privacyAccepted: boolean;
    aiPersonalization: boolean;
    marketingOptIn: boolean;
  };
};

type PlaceResult = {
  id: string;
  label: string;
  latitude: number;
  longitude: number;
  timezone: string;
  source: string;
};

type ChartSnapshot = {
  calculationEngine: string;
  ascendant: { sign: string; degree: number; nakshatra: string; pada: number };
  moon: { sign: string; degree: number; nakshatra: string; pada: number };
  sun: { sign: string; degree: number; nakshatra: string; pada: number };
  dasha: { mahadasha: string; antardasha: string };
  numerology: {
    birthNumber: number;
    lifePathNumber: number;
    personalYearNumber: number;
    personalDayNumber: number;
  };
};

type ReadingResponse = {
  headline: string;
  summary: string;
  love: string;
  career: string;
  money: string;
  mind: string;
  doActions: string[];
  dontActions: string[];
  luckySupports: { colors: string[]; numbers: number[]; mantra: string };
  astroEvidence: string[];
  safetyDisclaimer: string;
};

type ReportKind = "love" | "career" | "yearly";

const defaultProfile: BirthProfile = {
  birthDate: "2002-03-07",
  birthTime: "22:44",
  birthTimeConfidence: "exact",
  birthplaceText: "Umarga, Maharashtra, India",
  latitude: 17.8367,
  longitude: 76.6206,
  timezone: "Asia/Kolkata",
  language: "en-IN",
  consent: {
    privacyAccepted: false,
    aiPersonalization: true,
    marketingOptIn: false
  }
};

async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      "X-User-Id": "demo-user",
      ...(init?.headers ?? {})
    }
  });

  if (!res.ok) {
    const detail = await res.text();
    throw new Error(detail || `Request failed with ${res.status}`);
  }

  return res.json() as Promise<T>;
}

function Field({
  label,
  value,
  onChangeText,
  keyboardType
}: {
  label: string;
  value: string;
  onChangeText: (value: string) => void;
  keyboardType?: "default" | "numeric";
}) {
  return (
    <View style={styles.field}>
      <Text style={styles.label}>{label}</Text>
      <TextInput
        style={styles.input}
        value={value}
        onChangeText={onChangeText}
        keyboardType={keyboardType ?? "default"}
        autoCapitalize="none"
        placeholderTextColor="#778189"
      />
    </View>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <View style={styles.section}>
      <Text style={styles.sectionTitle}>{title}</Text>
      {children}
    </View>
  );
}

function Pill({ children }: { children: React.ReactNode }) {
  return (
    <View style={styles.pill}>
      <Text style={styles.pillText}>{children}</Text>
    </View>
  );
}

function ConsentToggle({
  label,
  value,
  onValueChange
}: {
  label: string;
  value: boolean;
  onValueChange: (value: boolean) => void;
}) {
  return (
    <Pressable style={styles.toggleRow} onPress={() => onValueChange(!value)}>
      <View style={[styles.checkbox, value && styles.checkboxActive]}>
        {value ? <Check color="#FFFFFF" size={15} /> : null}
      </View>
      <Text style={styles.toggleLabel}>{label}</Text>
    </Pressable>
  );
}

function normalizeProfile(raw: Partial<BirthProfile>): BirthProfile {
  return {
    ...defaultProfile,
    ...raw,
    consent: {
      ...defaultProfile.consent,
      ...(raw.consent ?? {})
    },
    birthTimeConfidence: raw.birthTimeConfidence ?? defaultProfile.birthTimeConfidence
  };
}

export default function App() {
  const [profile, setProfile] = useState<BirthProfile>(defaultProfile);
  const [placeQuery, setPlaceQuery] = useState(defaultProfile.birthplaceText);
  const [placeResults, setPlaceResults] = useState<PlaceResult[]>([]);
  const [placeLoading, setPlaceLoading] = useState(false);
  const [profileSaved, setProfileSaved] = useState(false);
  const [chart, setChart] = useState<ChartSnapshot | null>(null);
  const [reading, setReading] = useState<ReadingResponse | null>(null);
  const [askText, setAskText] = useState("What should I stop avoiding this week?");
  const [askAnswer, setAskAnswer] = useState<ReadingResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeReport, setActiveReport] = useState<ReportKind>("career");

  const canSubmit = useMemo(
    () =>
      profile.birthDate.length >= 10 &&
      profile.birthTime.length >= 4 &&
      Number.isFinite(profile.latitude) &&
      Number.isFinite(profile.longitude) &&
      profile.consent.privacyAccepted,
    [profile]
  );

  useEffect(() => {
    AsyncStorage.getItem(PROFILE_KEY).then((raw) => {
      if (raw) {
        const saved = normalizeProfile(JSON.parse(raw) as Partial<BirthProfile>);
        setProfile(saved);
        setPlaceQuery(saved.birthplaceText);
        setProfileSaved(true);
        void loadChartAndReading(saved);
      }
    });
  }, []);

  async function loadChartAndReading(currentProfile: BirthProfile) {
    setLoading(true);
    try {
      const [chartData, readingData] = await Promise.all([
        apiRequest<ChartSnapshot>("/chart/natal"),
        apiRequest<ReadingResponse>("/reading/daily")
      ]);
      setChart(chartData);
      setReading(readingData);
      await AsyncStorage.setItem(PROFILE_KEY, JSON.stringify(currentProfile));
    } catch (error) {
      Alert.alert("Reading unavailable", error instanceof Error ? error.message : "Please try again.");
    } finally {
      setLoading(false);
    }
  }

  async function saveProfile() {
    if (!canSubmit) {
      Alert.alert("Missing birth details", "Add birth date, time, coordinates, and accept privacy terms.");
      return;
    }

    setLoading(true);
    try {
      await apiRequest("/profile", {
        method: "POST",
        body: JSON.stringify(profile)
      });
      setProfileSaved(true);
      await loadChartAndReading(profile);
    } catch (error) {
      Alert.alert("Profile not saved", error instanceof Error ? error.message : "Please try again.");
      setLoading(false);
    }
  }

  async function searchBirthplace() {
    if (placeQuery.trim().length < 2) {
      Alert.alert("Birthplace needed", "Type at least two characters.");
      return;
    }
    setPlaceLoading(true);
    try {
      const data = await apiRequest<{ results: PlaceResult[] }>(`/places/search?q=${encodeURIComponent(placeQuery)}&limit=6`);
      setPlaceResults(data.results);
    } catch (error) {
      Alert.alert("Place search failed", error instanceof Error ? error.message : "Please try again.");
    } finally {
      setPlaceLoading(false);
    }
  }

  function selectPlace(place: PlaceResult) {
    setProfile((prev) => ({
      ...prev,
      birthplaceText: place.label,
      latitude: place.latitude,
      longitude: place.longitude,
      timezone: place.timezone
    }));
    setPlaceQuery(place.label);
    setPlaceResults([]);
  }

  async function scheduleDailyPing() {
    const permissions = await Notifications.requestPermissionsAsync();
    if (!permissions.granted) {
      Alert.alert("Notifications off", "Enable notifications to get your morning transit note.");
      return;
    }

    await Notifications.cancelAllScheduledNotificationsAsync();
    await Notifications.scheduleNotificationAsync({
      content: {
        title: "Your chart moved overnight",
        body: reading?.headline ?? "Open your Vedic reading for today."
      },
      trigger: {
        type: Notifications.SchedulableTriggerInputTypes.DAILY,
        hour: 8,
        minute: 7
      }
    });
    Alert.alert("Daily note set", "You will get a daily reading prompt at 8:07 AM.");
  }

  async function purchaseReport(kind: ReportKind) {
    setActiveReport(kind);
    try {
      const result = await apiRequest<{ status: string; unlocked: boolean; report: ReadingResponse }>("/reports/purchase", {
        method: "POST",
        body: JSON.stringify({
          reportKind: kind,
          productId: `trustastro_${kind}_report`,
          appUserId: "demo-user",
          receiptToken: "local-demo"
        })
      });
      setAskAnswer(result.report);
      Alert.alert(result.unlocked ? "Report unlocked" : "Purchase pending", result.report.headline);
    } catch (error) {
      Alert.alert("Purchase unavailable", error instanceof Error ? error.message : "Please try again.");
    }
  }

  async function askAstro() {
    try {
      const answer = await apiRequest<ReadingResponse>("/ask", {
        method: "POST",
        body: JSON.stringify({ question: askText })
      });
      setAskAnswer(answer);
    } catch (error) {
      Alert.alert("Ask failed", error instanceof Error ? error.message : "Please try again.");
    }
  }

  async function deleteAccount() {
    await apiRequest("/account", { method: "DELETE" });
    await AsyncStorage.removeItem(PROFILE_KEY);
    setProfileSaved(false);
    setChart(null);
    setReading(null);
    setAskAnswer(null);
  }

  return (
    <SafeAreaView style={styles.safeArea}>
      <StatusBar style="dark" />
      <KeyboardAvoidingView style={styles.screen} behavior={Platform.OS === "ios" ? "padding" : undefined}>
        <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
          <View style={styles.header}>
            <View style={styles.brandMark}>
              <MoonStar color="#F3F6F4" size={26} />
            </View>
            <View style={styles.headerText}>
              <Text style={styles.kicker}>Vedic + Numerology</Text>
              <Text style={styles.title}>Trust Astro</Text>
            </View>
          </View>

          <View style={styles.hero}>
            <Sparkles color="#C74634" size={22} />
            <Text style={styles.heroHeadline}>{reading?.headline ?? "Your chart does not need flattery. It needs receipts."}</Text>
            <Text style={styles.heroCopy}>
              {reading?.summary ??
                "Enter your birth details once. The backend computes the chart; GPT only turns the evidence into sharp, readable guidance."}
            </Text>
          </View>

          <Section title="Birth Profile">
            <Field
              label="Birth date"
              value={profile.birthDate}
              onChangeText={(birthDate) => setProfile((prev) => ({ ...prev, birthDate }))}
            />
            <Field
              label="Birth time"
              value={profile.birthTime}
              onChangeText={(birthTime) => setProfile((prev) => ({ ...prev, birthTime }))}
            />
            <View style={styles.choiceRow}>
              {(["exact", "approximate", "unknown"] as BirthProfile["birthTimeConfidence"][]).map((choice) => (
                <Pressable
                  key={choice}
                  style={[styles.choiceButton, profile.birthTimeConfidence === choice && styles.choiceButtonActive]}
                  onPress={() => setProfile((prev) => ({ ...prev, birthTimeConfidence: choice }))}
                >
                  <Text style={[styles.choiceText, profile.birthTimeConfidence === choice && styles.choiceTextActive]}>{choice}</Text>
                </Pressable>
              ))}
            </View>
            <Field
              label="Birthplace search"
              value={placeQuery}
              onChangeText={setPlaceQuery}
            />
            <Pressable style={styles.secondaryButton} onPress={searchBirthplace}>
              {placeLoading ? <ActivityIndicator color="#101820" /> : <Search color="#101820" size={18} />}
              <Text style={styles.secondaryButtonText}>Search Place</Text>
            </Pressable>
            {placeResults.map((place) => (
              <Pressable key={place.id} style={styles.placeResult} onPress={() => selectPlace(place)}>
                <MapPin color="#2F6D58" size={18} />
                <View style={styles.placeTextWrap}>
                  <Text style={styles.placeTitle}>{place.label}</Text>
                  <Text style={styles.placeMeta}>{place.timezone}</Text>
                </View>
              </Pressable>
            ))}
            <Pill>{profile.birthplaceText} / {profile.timezone}</Pill>
            <View style={styles.consentGroup}>
              <ConsentToggle
                label="I accept the privacy terms for storing my birth profile."
                value={profile.consent.privacyAccepted}
                onValueChange={(privacyAccepted) =>
                  setProfile((prev) => ({
                    ...prev,
                    consent: { ...prev.consent, privacyAccepted }
                  }))
                }
              />
              <ConsentToggle
                label="Use my chart context for GPT-personalized readings."
                value={profile.consent.aiPersonalization}
                onValueChange={(aiPersonalization) =>
                  setProfile((prev) => ({
                    ...prev,
                    consent: { ...prev.consent, aiPersonalization }
                  }))
                }
              />
              <ConsentToggle
                label="Send occasional launch and report updates."
                value={profile.consent.marketingOptIn}
                onValueChange={(marketingOptIn) =>
                  setProfile((prev) => ({
                    ...prev,
                    consent: { ...prev.consent, marketingOptIn }
                  }))
                }
              />
            </View>
            <Pressable style={[styles.primaryButton, !canSubmit && styles.disabledButton]} onPress={saveProfile} disabled={!canSubmit || loading}>
              {loading ? <ActivityIndicator color="#F3F6F4" /> : <CalendarDays color="#F3F6F4" size={20} />}
              <Text style={styles.primaryButtonText}>{profileSaved ? "Refresh Reading" : "Save Birth Profile"}</Text>
            </Pressable>
          </Section>

          {chart ? (
            <Section title="Natal Receipts">
              <View style={styles.receiptsGrid}>
                <Pill>Asc {chart.ascendant.sign} {chart.ascendant.degree.toFixed(1)} deg</Pill>
                <Pill>Moon {chart.moon.sign} / {chart.moon.nakshatra}</Pill>
                <Pill>Sun {chart.sun.sign}</Pill>
                <Pill>Dasha {chart.dasha.mahadasha}</Pill>
                <Pill>Life Path {chart.numerology.lifePathNumber}</Pill>
                <Pill>Personal Day {chart.numerology.personalDayNumber}</Pill>
                <Pill>{chart.calculationEngine.split("+").at(0)?.trim() ?? chart.calculationEngine}</Pill>
              </View>
            </Section>
          ) : null}

          {reading ? (
            <Section title="Today">
              <Text style={styles.bodyText}>{reading.love}</Text>
              <Text style={styles.bodyText}>{reading.career}</Text>
              <Text style={styles.bodyText}>{reading.money}</Text>
              <Text style={styles.bodyText}>{reading.mind}</Text>
              <View style={styles.actionGrid}>
                {reading.doActions.map((item) => (
                  <Pill key={`do-${item}`}>Do: {item}</Pill>
                ))}
                {reading.dontActions.map((item) => (
                  <Pill key={`dont-${item}`}>Skip: {item}</Pill>
                ))}
              </View>
              <View style={styles.evidenceBox}>
                {reading.astroEvidence.map((item) => (
                  <Text style={styles.evidenceText} key={item}>{item}</Text>
                ))}
              </View>
              <Pressable style={styles.secondaryButton} onPress={scheduleDailyPing}>
                <Bell color="#101820" size={18} />
                <Text style={styles.secondaryButtonText}>Set Daily Push</Text>
              </Pressable>
            </Section>
          ) : null}

          <Section title="Paid Reports">
            <View style={styles.segment}>
              {(["love", "career", "yearly"] as ReportKind[]).map((kind) => (
                <Pressable
                  key={kind}
                  style={[styles.segmentButton, activeReport === kind && styles.segmentButtonActive]}
                  onPress={() => purchaseReport(kind)}
                >
                  <Text style={[styles.segmentText, activeReport === kind && styles.segmentTextActive]}>{kind}</Text>
                </Pressable>
              ))}
            </View>
          </Section>

          <Section title="Ask">
            <Field label="Question" value={askText} onChangeText={setAskText} />
            <Pressable style={styles.secondaryButton} onPress={askAstro}>
              <MessageCircle color="#101820" size={18} />
              <Text style={styles.secondaryButtonText}>Ask With Chart Context</Text>
            </Pressable>
            {askAnswer ? (
              <View style={styles.answerBox}>
                <Text style={styles.answerTitle}>{askAnswer.headline}</Text>
                <Text style={styles.bodyText}>{askAnswer.summary}</Text>
              </View>
            ) : null}
          </Section>

          <Pressable style={styles.deleteButton} onPress={deleteAccount}>
            <Trash2 color="#8D2F23" size={18} />
            <Text style={styles.deleteText}>Delete account data</Text>
          </Pressable>

          <Text style={styles.disclaimer}>
            {reading?.safetyDisclaimer ??
              "Astrology is reflective guidance, not medical, legal, financial, or crisis advice."}
          </Text>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: "#F3F6F4"
  },
  screen: {
    flex: 1
  },
  content: {
    padding: 20,
    gap: 18
  },
  header: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    marginTop: 8
  },
  brandMark: {
    width: 52,
    height: 52,
    borderRadius: 8,
    backgroundColor: "#101820",
    alignItems: "center",
    justifyContent: "center"
  },
  headerText: {
    flex: 1
  },
  kicker: {
    color: "#6F5E46",
    fontSize: 12,
    textTransform: "uppercase",
    letterSpacing: 0,
    fontWeight: "700"
  },
  title: {
    color: "#101820",
    fontSize: 33,
    fontWeight: "800",
    letterSpacing: 0
  },
  hero: {
    backgroundColor: "#F7DED6",
    borderRadius: 8,
    padding: 18,
    gap: 10,
    borderWidth: 1,
    borderColor: "#DAA99B"
  },
  heroHeadline: {
    color: "#101820",
    fontSize: 25,
    lineHeight: 31,
    fontWeight: "800",
    letterSpacing: 0
  },
  heroCopy: {
    color: "#3A3F43",
    fontSize: 15,
    lineHeight: 22
  },
  section: {
    gap: 12,
    paddingVertical: 2
  },
  sectionTitle: {
    color: "#101820",
    fontSize: 18,
    fontWeight: "800"
  },
  field: {
    gap: 6
  },
  label: {
    color: "#3A3F43",
    fontSize: 13,
    fontWeight: "700"
  },
  input: {
    height: 46,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#BFC8C1",
    backgroundColor: "#FFFFFF",
    color: "#101820",
    paddingHorizontal: 12,
    fontSize: 16
  },
  row: {
    flexDirection: "row",
    gap: 12
  },
  half: {
    flex: 1
  },
  choiceRow: {
    flexDirection: "row",
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#5A7167",
    overflow: "hidden"
  },
  choiceButton: {
    flex: 1,
    minHeight: 42,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#FFFFFF"
  },
  choiceButtonActive: {
    backgroundColor: "#2F6D58"
  },
  choiceText: {
    color: "#2F3B36",
    fontSize: 12,
    fontWeight: "800",
    textTransform: "capitalize"
  },
  choiceTextActive: {
    color: "#FFFFFF"
  },
  placeResult: {
    flexDirection: "row",
    gap: 10,
    alignItems: "center",
    minHeight: 58,
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderRadius: 8,
    backgroundColor: "#FFFFFF",
    borderWidth: 1,
    borderColor: "#BFC8C1"
  },
  placeTextWrap: {
    flex: 1,
    gap: 2
  },
  placeTitle: {
    color: "#101820",
    fontSize: 14,
    lineHeight: 19,
    fontWeight: "800"
  },
  placeMeta: {
    color: "#5F6B65",
    fontSize: 12,
    fontWeight: "700"
  },
  consentGroup: {
    gap: 10
  },
  toggleRow: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 10,
    paddingVertical: 2
  },
  checkbox: {
    width: 22,
    height: 22,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: "#5A7167",
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#FFFFFF",
    marginTop: 1
  },
  checkboxActive: {
    backgroundColor: "#2F6D58",
    borderColor: "#2F6D58"
  },
  toggleLabel: {
    flex: 1,
    color: "#2D3236",
    fontSize: 13,
    lineHeight: 18,
    fontWeight: "700"
  },
  primaryButton: {
    height: 50,
    borderRadius: 8,
    backgroundColor: "#101820",
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8
  },
  disabledButton: {
    opacity: 0.45
  },
  primaryButtonText: {
    color: "#F3F6F4",
    fontSize: 16,
    fontWeight: "800"
  },
  secondaryButton: {
    height: 48,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#101820",
    backgroundColor: "#FFFFFF",
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8
  },
  secondaryButtonText: {
    color: "#101820",
    fontSize: 15,
    fontWeight: "800"
  },
  receiptsGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8
  },
  pill: {
    borderRadius: 8,
    backgroundColor: "#DDE8DF",
    paddingHorizontal: 10,
    paddingVertical: 8,
    maxWidth: "100%"
  },
  pillText: {
    color: "#17362B",
    fontSize: 13,
    fontWeight: "700"
  },
  bodyText: {
    color: "#2D3236",
    fontSize: 15,
    lineHeight: 22
  },
  actionGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8
  },
  evidenceBox: {
    gap: 8,
    backgroundColor: "#FFFFFF",
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#BFC8C1",
    padding: 12
  },
  evidenceText: {
    color: "#4A4239",
    fontSize: 13,
    lineHeight: 19
  },
  segment: {
    flexDirection: "row",
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#101820",
    overflow: "hidden"
  },
  segmentButton: {
    flex: 1,
    minHeight: 46,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#FFFFFF"
  },
  segmentButtonActive: {
    backgroundColor: "#101820"
  },
  segmentText: {
    color: "#101820",
    fontSize: 14,
    fontWeight: "800",
    textTransform: "capitalize"
  },
  segmentTextActive: {
    color: "#F3F6F4"
  },
  answerBox: {
    borderRadius: 8,
    backgroundColor: "#EEF5FF",
    borderWidth: 1,
    borderColor: "#B8C9E6",
    padding: 12,
    gap: 8
  },
  answerTitle: {
    color: "#101820",
    fontSize: 17,
    fontWeight: "800"
  },
  deleteButton: {
    height: 44,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#CFA49B",
    backgroundColor: "#FFF2EF",
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8
  },
  deleteText: {
    color: "#8D2F23",
    fontSize: 14,
    fontWeight: "800"
  },
  disclaimer: {
    color: "#6C6257",
    fontSize: 12,
    lineHeight: 18,
    paddingBottom: 24
  }
});
