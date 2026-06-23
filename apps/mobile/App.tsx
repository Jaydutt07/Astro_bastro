import AsyncStorage from "@react-native-async-storage/async-storage";
import { LinearGradient } from "expo-linear-gradient";
import * as Notifications from "expo-notifications";
import { StatusBar } from "expo-status-bar";
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
import {
  Bell,
  CalendarDays,
  Check,
  Crown,
  Flame,
  Hash,
  HeartHandshake,
  Lock,
  MapPin,
  MessageCircle,
  MoonStar,
  Search,
  Settings,
  ShieldCheck,
  Sparkles,
  Trash2,
  UserRound
} from "lucide-react-native";

const API_BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL ?? (Platform.OS === "android" ? "http://10.0.2.2:8000" : "http://127.0.0.1:8000");
const PROFILE_KEY = "astrosolves.profile";

type ReadingPeriod = "daily" | "weekly" | "monthly" | "yearly";
type ProblemCategory = "shani" | "relationship" | "career" | "money" | "family" | "health-stress" | "other";
type RelationshipFocus = "relationship" | "marriage" | "peace";
type AppTab = "profile" | "readings" | "harmony" | "problems" | "premium" | "settings";

type EntitlementStatus = {
  access: string;
  freeLimit: number;
  freeUsed: number;
  freeRemaining: number;
  message: string;
};

type EntitlementsResponse = {
  reading: EntitlementStatus;
  problem: EntitlementStatus;
};

type MemoryContextResponse = {
  memory: {
    problemCount: number;
    recentProblems: Array<{ category: string; problemTitle?: string; problemDetails?: string; createdAt?: string }>;
    categoryCounts: Record<string, number>;
    solutionHistory: Array<{ title?: string; duration?: string; createdAt?: string }>;
  };
};

type BirthProfile = {
  fullName: string;
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

type ZodiacPoint = {
  sign: string;
  degree: number;
  nakshatra: string;
  pada: number;
};

type PlanetTransit = {
  planet: string;
  point: ZodiacPoint;
  house: number;
};

type ChartSnapshot = {
  calculationEngine: string;
  ascendant: ZodiacPoint;
  moon: ZodiacPoint;
  sun: ZodiacPoint;
  dasha: { mahadasha: string; antardasha: string };
  numerology: {
    birthNumber: number;
    lifePathNumber: number;
    personalYearNumber: number;
    personalDayNumber: number;
  };
  transits?: PlanetTransit[];
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
  entitlement?: EntitlementStatus;
};

type SolutionStep = {
  title: string;
  practice: string;
  duration: string;
  why: string;
  isFree: boolean;
};

type ProblemInsightResponse = {
  problemTitle: string;
  reassurance: string;
  astroPattern: string;
  timeline: string;
  watchouts: string[];
  freeSolution: SolutionStep;
  premiumSolutions: SolutionStep[];
  astroEvidence: string[];
  safetyDisclaimer: string;
  entitlement?: EntitlementStatus;
};

type HarmonyPerson = {
  name: string;
  sign: string;
  birthNumber?: number | null;
  lifePathNumber?: number | null;
  nameNumber: number;
};

type HarmonyResponse = {
  title: string;
  compatibilityScore: number;
  user: HarmonyPerson;
  partner: HarmonyPerson;
  bestRelationshipMatches: string[];
  bestMarriageMatches: string[];
  challengingMatches: string[];
  relationshipLens: string;
  marriageLens: string;
  numerologyLens: string;
  peacePractice: string;
  watchouts: string[];
  remedies: string[];
  astroEvidence: string[];
  safetyDisclaimer: string;
};

const defaultProfile: BirthProfile = {
  fullName: "Astro Solves Seeker",
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

const periodOptions: Array<{ key: ReadingPeriod; label: string }> = [
  { key: "daily", label: "Daily" },
  { key: "weekly", label: "Weekly" },
  { key: "monthly", label: "Monthly" },
  { key: "yearly", label: "Yearly" }
];

const tabOptions: Array<{ key: AppTab; label: string }> = [
  { key: "profile", label: "Profile" },
  { key: "readings", label: "Reading" },
  { key: "harmony", label: "Harmony" },
  { key: "problems", label: "Problems" },
  { key: "premium", label: "Royal" }
];

const categories: Array<{ key: ProblemCategory; label: string }> = [
  { key: "shani", label: "Shani" },
  { key: "relationship", label: "Relationship" },
  { key: "career", label: "Career" },
  { key: "money", label: "Money" },
  { key: "family", label: "Family" },
  { key: "health-stress", label: "Stress" },
  { key: "other", label: "Other" }
];

const paidIdeas = [
  {
    title: "Extra Period Readings",
    body: "Open daily, weekly, monthly, and yearly guidance on the same day after the free choice is used."
  },
  {
    title: "Deep Problem Map",
    body: "Long-form root pattern, likely phases, watchouts, and practical remedies for one serious concern."
  },
  {
    title: "Remedy Audio Vault",
    body: "Guided Hanuman Chalisa, Shani discipline, breath resets, and ritual reminders."
  },
  {
    title: "21-Day Shani Care",
    body: "A calm accountability path for delays, fear, repeated pressure, and Saade Saati themes."
  }
];

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
    let message = detail;
    try {
      const parsed = JSON.parse(detail) as { detail?: string };
      message = parsed.detail || detail;
    } catch {
      message = detail;
    }
    throw new Error(message || `Request failed with ${res.status}`);
  }

  return res.json() as Promise<T>;
}

function normalizeProfile(raw: Partial<BirthProfile>): BirthProfile {
  return {
    ...defaultProfile,
    ...raw,
    fullName: raw.fullName ?? defaultProfile.fullName,
    consent: {
      ...defaultProfile.consent,
      ...(raw.consent ?? {})
    },
    birthTimeConfidence: raw.birthTimeConfidence ?? defaultProfile.birthTimeConfidence
  };
}

function titleCasePeriod(period: ReadingPeriod): string {
  return period.charAt(0).toUpperCase() + period.slice(1);
}

function SectionHeader({ eyebrow, title }: { eyebrow: string; title: string }) {
  return (
    <View style={styles.sectionHeader}>
      <Text style={styles.kicker}>{eyebrow}</Text>
      <Text style={styles.sectionTitle}>{title}</Text>
    </View>
  );
}

function Field({
  label,
  value,
  onChangeText,
  keyboardType,
  multiline,
  placeholder,
  testID
}: {
  label: string;
  value: string;
  onChangeText: (value: string) => void;
  keyboardType?: "default" | "numeric";
  multiline?: boolean;
  placeholder?: string;
  testID?: string;
}) {
  return (
    <View style={styles.field}>
      <Text style={styles.label}>{label}</Text>
      <TextInput
        style={[styles.input, multiline && styles.textArea]}
        value={value}
        onChangeText={onChangeText}
        keyboardType={keyboardType ?? "default"}
        multiline={multiline}
        numberOfLines={multiline ? 5 : 1}
        textAlignVertical={multiline ? "top" : "center"}
        autoCapitalize="none"
        placeholder={placeholder}
        placeholderTextColor="#857D72"
        testID={testID}
      />
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
    <Pressable accessibilityRole="button" testID={`toggle-${label.slice(0, 12).toLowerCase().replaceAll(" ", "-")}`} style={styles.toggleRow} onPress={() => onValueChange(!value)}>
      <View style={[styles.checkbox, value && styles.checkboxActive]}>
        {value ? <Check color="#FFF8EA" size={15} strokeWidth={3} /> : null}
      </View>
      <Text style={styles.toggleLabel}>{label}</Text>
    </Pressable>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.metricCard}>
      <Text style={styles.metricLabel}>{label}</Text>
      <Text style={styles.metricValue}>{value}</Text>
    </View>
  );
}

function Pill({ children, tone = "green" }: { children: React.ReactNode; tone?: "green" | "gold" | "ruby" | "ink" }) {
  return (
    <View style={[styles.pill, styles[`${tone}Pill`]]}>
      <Text style={[styles.pillText, tone === "ink" && styles.inkPillText]}>{children}</Text>
    </View>
  );
}

function EntitlementPanel({ label, status }: { label: string; status?: EntitlementStatus | null }) {
  const fallbackLimit = label.toLowerCase().includes("problem") ? 2 : 1;
  const remaining = status?.freeRemaining ?? fallbackLimit;
  const limit = status?.freeLimit ?? fallbackLimit;
  const used = status?.freeUsed ?? 0;
  return (
    <View style={styles.entitlementPanel}>
      <View style={styles.entitlementTop}>
        <Text style={styles.entitlementLabel}>{label}</Text>
        <Text style={styles.entitlementCount}>{remaining}/{limit}</Text>
      </View>
      <Text style={styles.entitlementMessage}>{status?.message ?? "Save your profile to open free beta access."}</Text>
      <View style={styles.entitlementTrack}>
        <View style={[styles.entitlementFill, { width: `${limit ? Math.min(100, (used / limit) * 100) : 0}%` }]} />
      </View>
    </View>
  );
}

function CosmicMap() {
  return (
    <View style={styles.cosmicMap}>
      <View style={styles.cosmicPlate} />
      <View style={styles.orbitOuter} />
      <View style={styles.orbitMiddle} />
      <View style={styles.orbitInner} />
      <View style={[styles.starDot, styles.starOne]} />
      <View style={[styles.starDot, styles.starTwo]} />
      <View style={[styles.starDot, styles.starThree]} />
      <View style={[styles.starDot, styles.starFour]} />
      <MoonStar color="#FFF8EA" size={34} strokeWidth={1.8} />
    </View>
  );
}

function CardCrest({ title }: { title: string }) {
  return (
    <View style={styles.cardCrest}>
      <View style={styles.crestGem} />
      <Text style={styles.cardCrestText}>{title}</Text>
      <View style={styles.crestLine} />
    </View>
  );
}

function ReadingLane({ title, body }: { title: string; body: string }) {
  return (
    <View style={styles.readingLane}>
      <Text style={styles.laneTitle}>{title}</Text>
      <Text style={styles.bodyText}>{body}</Text>
    </View>
  );
}

function SolutionCard({ step, locked }: { step: SolutionStep; locked: boolean }) {
  return (
    <View style={[styles.solutionCard, locked && styles.lockedSolutionCard]}>
      <View style={styles.solutionHeader}>
        <View style={[styles.solutionIcon, locked ? styles.lockedIcon : styles.freeIcon]}>
          {locked ? <Lock color="#FFF8EA" size={17} /> : <Flame color="#4A2516" size={18} />}
        </View>
        <View style={styles.solutionTitleWrap}>
          <Text style={styles.solutionTitle}>{step.title}</Text>
          <Text style={styles.solutionMeta}>{step.duration}</Text>
        </View>
      </View>
      <Text style={styles.bodyText}>{step.practice}</Text>
      <Text style={styles.solutionWhy}>{step.why}</Text>
    </View>
  );
}

function saturnTransitLabel(chart: ChartSnapshot | null): string {
  const saturn = chart?.transits?.find((item) => item.planet === "Saturn");
  if (!saturn) {
    return "Saturn pending";
  }
  return `${saturn.point.sign} / H${saturn.house}`;
}

export default function App() {
  const [profile, setProfile] = useState<BirthProfile>(defaultProfile);
  const [activeTab, setActiveTab] = useState<AppTab>("profile");
  const [placeQuery, setPlaceQuery] = useState(defaultProfile.birthplaceText);
  const [placeResults, setPlaceResults] = useState<PlaceResult[]>([]);
  const [placeLoading, setPlaceLoading] = useState(false);
  const [profileSaved, setProfileSaved] = useState(false);
  const [chart, setChart] = useState<ChartSnapshot | null>(null);
  const [reading, setReading] = useState<ReadingResponse | null>(null);
  const [activePeriod, setActivePeriod] = useState<ReadingPeriod>("daily");
  const [profileLoading, setProfileLoading] = useState(false);
  const [readingLoading, setReadingLoading] = useState(false);
  const [problemCategory, setProblemCategory] = useState<ProblemCategory>("shani");
  const [problemDetails, setProblemDetails] = useState("I feel blocked in career and worried this is connected to Saade Saati.");
  const [problemInsight, setProblemInsight] = useState<ProblemInsightResponse | null>(null);
  const [entitlements, setEntitlements] = useState<EntitlementsResponse | null>(null);
  const [memoryContext, setMemoryContext] = useState<MemoryContextResponse["memory"] | null>(null);
  const [partnerName, setPartnerName] = useState("Aarohi Sharma");
  const [partnerBirthDate, setPartnerBirthDate] = useState("2001-08-14");
  const [relationshipFocus, setRelationshipFocus] = useState<RelationshipFocus>("relationship");
  const [harmonyInsight, setHarmonyInsight] = useState<HarmonyResponse | null>(null);
  const [harmonyLoading, setHarmonyLoading] = useState(false);
  const [problemLoading, setProblemLoading] = useState(false);
  const [solutionLoading, setSolutionLoading] = useState(false);
  const [solutionUnlocked, setSolutionUnlocked] = useState(false);
  const [selectedPaidIdea, setSelectedPaidIdea] = useState(paidIdeas[0]?.title ?? "Extra Period Readings");
  const [statusMessage, setStatusMessage] = useState("Ready for your birth details.");

  const canSubmit = useMemo(
    () =>
      profile.fullName.trim().length >= 2 &&
      profile.birthDate.length >= 10 &&
      profile.birthTime.length >= 4 &&
      Number.isFinite(profile.latitude) &&
      Number.isFinite(profile.longitude) &&
      profile.consent.privacyAccepted,
    [profile]
  );
  const freeProblemSolutionOpen = solutionUnlocked && (problemInsight?.entitlement?.access === "free" || (problemInsight?.entitlement?.freeUsed ?? 0) <= 2);

  useEffect(() => {
    let mounted = true;
    AsyncStorage.getItem(PROFILE_KEY).then((raw) => {
      if (!mounted || !raw) {
        return;
      }
      const saved = normalizeProfile(JSON.parse(raw) as Partial<BirthProfile>);
      setProfile(saved);
      setPlaceQuery(saved.birthplaceText);
      setProfileSaved(true);
      void loadChart(saved);
      void fetchEntitlements();
      void fetchMemoryContext();
    });
    return () => {
      mounted = false;
    };
  }, []);

  async function fetchEntitlements() {
    try {
      const data = await apiRequest<EntitlementsResponse>("/entitlements");
      setEntitlements(data);
    } catch {
      setEntitlements(null);
    }
  }

  async function fetchMemoryContext() {
    try {
      const data = await apiRequest<MemoryContextResponse>("/memory/context");
      setMemoryContext(data.memory);
    } catch {
      setMemoryContext(null);
    }
  }

  async function loadChart(currentProfile: BirthProfile) {
    setProfileLoading(true);
    setStatusMessage(`Opening chart for ${currentProfile.fullName}...`);
    try {
      const chartData = await apiRequest<ChartSnapshot>("/chart/natal");
      setChart(chartData);
      await AsyncStorage.setItem(PROFILE_KEY, JSON.stringify(currentProfile));
      setStatusMessage(`Chart ready for ${currentProfile.fullName}. Choose today's free reading.`);
    } catch (error) {
      setStatusMessage("Chart could not be opened. Check the API and try again.");
      Alert.alert("Chart unavailable", error instanceof Error ? error.message : "Please try again.");
    } finally {
      setProfileLoading(false);
    }
  }

  function selectReadingPeriod(period: ReadingPeriod) {
    setActivePeriod(period);
    setStatusMessage(`${titleCasePeriod(period)} selected for today's free reading.`);
  }

  async function unlockPeriodReading() {
    if (!profileSaved) {
      setStatusMessage("Save your birth profile before opening a reading.");
      return;
    }
    setReadingLoading(true);
    setStatusMessage(`Opening ${activePeriod} reading...`);
    try {
      const readingData = await apiRequest<ReadingResponse>(`/reading/${activePeriod}`);
      setReading(readingData);
      if (readingData.entitlement) {
        setEntitlements((prev) => ({
          reading: readingData.entitlement as EntitlementStatus,
          problem: prev?.problem ?? entitlements?.problem ?? {
            access: "free",
            freeLimit: 2,
            freeUsed: 0,
            freeRemaining: 2,
            message: "2 free problem analyses left."
          }
        }));
      } else {
        await fetchEntitlements();
      }
      setStatusMessage(`${titleCasePeriod(activePeriod)} reading is ready.`);
    } catch (error) {
      setStatusMessage(error instanceof Error ? error.message : "Period reading could not be generated.");
      Alert.alert("Reading unavailable", error instanceof Error ? error.message : "Please try again.");
    } finally {
      setReadingLoading(false);
    }
  }

  async function saveProfile() {
    if (!canSubmit) {
      setStatusMessage("Add birth details, select a place, and accept privacy storage before saving.");
      Alert.alert("Birth profile needed", "Add name, birth details, place, and privacy consent.");
      return;
    }

    setProfileLoading(true);
    setStatusMessage("Saving profile and preparing chart...");
    try {
      await apiRequest<BirthProfile>("/profile", {
        method: "POST",
        body: JSON.stringify(profile)
      });
      setProfileSaved(true);
      await AsyncStorage.setItem(PROFILE_KEY, JSON.stringify(profile));
      await loadChart(profile);
      await fetchEntitlements();
      await fetchMemoryContext();
      setActiveTab("readings");
    } catch (error) {
      setStatusMessage("Profile save failed. Check the API and try again.");
      Alert.alert("Profile not saved", error instanceof Error ? error.message : "Please try again.");
      setProfileLoading(false);
    }
  }

  async function searchBirthplace() {
    if (placeQuery.trim().length < 2) {
      setStatusMessage("Type at least two characters to search a birthplace.");
      Alert.alert("Birthplace needed", "Type at least two characters.");
      return;
    }
    setPlaceLoading(true);
    setStatusMessage(`Searching places for "${placeQuery.trim()}"...`);
    try {
      const data = await apiRequest<{ results: PlaceResult[] }>(`/places/search?q=${encodeURIComponent(placeQuery)}&limit=6`);
      setPlaceResults(data.results);
      setStatusMessage(data.results.length ? `${data.results.length} place option${data.results.length === 1 ? "" : "s"} found.` : "No place matches found. Try a nearby city.");
    } catch (error) {
      setStatusMessage("Place search failed. Check the API and try again.");
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
    setStatusMessage(`Selected ${place.label}.`);
  }

  async function analyzeProblem() {
    if (!profileSaved) {
      setStatusMessage("Save your birth profile before analyzing a problem.");
      Alert.alert("Save profile first", "Astro Solves needs your chart before reading the problem.");
      return;
    }
    if (problemDetails.trim().length < 10) {
      setStatusMessage("Add more detail so the problem reading has enough context.");
      Alert.alert("Problem details needed", "Add a little more context.");
      return;
    }
    setProblemLoading(true);
    setSolutionUnlocked(false);
    setStatusMessage("Analyzing the astrological pattern behind your problem...");
    try {
      const insight = await apiRequest<ProblemInsightResponse>("/problem/insight", {
        method: "POST",
        body: JSON.stringify({
          category: problemCategory,
          problemDetails
        })
      });
      setProblemInsight(insight);
      setSolutionUnlocked(true);
      if (insight.entitlement) {
        setEntitlements((prev) => ({
          reading: prev?.reading ?? entitlements?.reading ?? {
            access: "free",
            freeLimit: 1,
            freeUsed: 0,
            freeRemaining: 1,
            message: "Choose one free period reading today."
          },
          problem: insight.entitlement as EntitlementStatus
        }));
      } else {
        await fetchEntitlements();
      }
      await fetchMemoryContext();
      setStatusMessage("Problem insight is ready. Free solution paths are open.");
    } catch (error) {
      setStatusMessage(error instanceof Error ? error.message : "Problem reading could not be generated.");
      Alert.alert("Problem reading unavailable", error instanceof Error ? error.message : "Please try again.");
    } finally {
      setProblemLoading(false);
    }
  }

  async function unlockSolutions() {
    if (!profileSaved) {
      setStatusMessage("Save your birth profile before unlocking solution packs.");
      Alert.alert("Save profile first", "Solution packs need your chart context.");
      return;
    }
    setSolutionLoading(true);
    setStatusMessage("Unlocking the solution pack...");
    try {
      const result = await apiRequest<{ unlocked: boolean; message: string; solutionPack: SolutionStep[] }>("/solutions/unlock", {
        method: "POST",
        body: JSON.stringify({
          productId: "astrosolves_solution_subscription",
          appUserId: "demo-user",
          receiptToken: "local-demo",
          category: problemCategory,
          problemDetails
        })
      });
      setSolutionUnlocked(result.unlocked);
      if (problemInsight) {
        setProblemInsight({ ...problemInsight, premiumSolutions: result.solutionPack });
      }
      setStatusMessage(result.unlocked ? "Solution pack unlocked." : "Solution verification is pending.");
      Alert.alert(result.unlocked ? "Solutions unlocked" : "Verification pending", result.message);
    } catch (error) {
      setStatusMessage("Solution unlock failed. Try again.");
      Alert.alert("Unlock unavailable", error instanceof Error ? error.message : "Please try again.");
    } finally {
      setSolutionLoading(false);
    }
  }

  async function generateHarmony() {
    if (!profileSaved) {
      setStatusMessage("Save your birth profile before opening Harmony.");
      Alert.alert("Save profile first", "Harmony uses your chart, sign, and numerology.");
      return;
    }
    if (partnerName.trim().length < 2) {
      setStatusMessage("Add your partner's name for numerology.");
      Alert.alert("Partner name needed", "Add at least two characters.");
      return;
    }
    setHarmonyLoading(true);
    setStatusMessage("Building relationship harmony map...");
    try {
      const harmony = await apiRequest<HarmonyResponse>("/harmony/insight", {
        method: "POST",
        body: JSON.stringify({
          partnerName,
          partnerBirthDate: partnerBirthDate.trim() || null,
          relationshipFocus
        })
      });
      setHarmonyInsight(harmony);
      setStatusMessage(`Harmony map ready with ${harmony.compatibilityScore}% resonance.`);
    } catch (error) {
      setStatusMessage("Harmony map could not be generated.");
      Alert.alert("Harmony unavailable", error instanceof Error ? error.message : "Please try again.");
    } finally {
      setHarmonyLoading(false);
    }
  }

  async function saveSettings() {
    if (!canSubmit) {
      setStatusMessage("Profile details are incomplete, so settings could not be saved.");
      Alert.alert("Profile needed", "Complete your birth profile before saving settings.");
      return;
    }
    setProfileLoading(true);
    setStatusMessage("Saving settings...");
    try {
      await apiRequest<BirthProfile>("/profile", {
        method: "POST",
        body: JSON.stringify(profile)
      });
      await AsyncStorage.setItem(PROFILE_KEY, JSON.stringify(profile));
      await fetchEntitlements();
      await fetchMemoryContext();
      setStatusMessage("Settings saved.");
    } catch (error) {
      setStatusMessage("Settings could not be saved.");
      Alert.alert("Settings unavailable", error instanceof Error ? error.message : "Please try again.");
    } finally {
      setProfileLoading(false);
    }
  }

  async function scheduleDailyPing() {
    try {
      setStatusMessage("Checking notification permission...");
      const permissions = await Notifications.requestPermissionsAsync();
      if (!permissions.granted) {
        setStatusMessage("Notifications are off. Enable them to receive daily reminders.");
        Alert.alert("Notifications off", "Enable notifications to get your morning transit note.");
        return;
      }

      await Notifications.cancelAllScheduledNotificationsAsync();
      await Notifications.scheduleNotificationAsync({
        content: {
          title: "Astro Solves",
          body: reading?.headline ?? "Your chart has a new daily note."
        },
        trigger: {
          type: Notifications.SchedulableTriggerInputTypes.DAILY,
          hour: 8,
          minute: 7
        }
      });
      setStatusMessage("Daily reading reminder set for 8:07 AM.");
      Alert.alert("Daily note set", "You will get a daily reading prompt at 8:07 AM.");
    } catch {
      setStatusMessage("Daily reminder is unavailable in this preview environment.");
      Alert.alert("Reminder unavailable", "Notifications may not be supported in this preview environment.");
    }
  }

  async function deleteAccount() {
    setStatusMessage("Deleting local account data...");
    try {
      await apiRequest("/account", { method: "DELETE" });
    } catch {
      // Local data still clears if the API is unavailable.
    }
    await AsyncStorage.removeItem(PROFILE_KEY);
    setProfileSaved(false);
    setChart(null);
    setReading(null);
    setProblemInsight(null);
    setHarmonyInsight(null);
    setEntitlements(null);
    setMemoryContext(null);
    setSolutionUnlocked(false);
    setActiveTab("profile");
    setStatusMessage("Account data cleared from this beta session.");
  }

  function renderTabIcon(tab: AppTab, active: boolean) {
    const color = active ? "#FFF8EA" : "#CBA45A";
    if (tab === "profile") {
      return <UserRound color={color} size={17} />;
    }
    if (tab === "readings") {
      return <CalendarDays color={color} size={17} />;
    }
    if (tab === "problems") {
      return <MessageCircle color={color} size={17} />;
    }
    if (tab === "harmony") {
      return <HeartHandshake color={color} size={17} />;
    }
    return <Crown color={color} size={17} />;
  }

  return (
    <SafeAreaView style={styles.safeArea}>
      <StatusBar style="light" />
      <KeyboardAvoidingView style={styles.screen} behavior={Platform.OS === "ios" ? "padding" : undefined}>
        <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
          <View style={styles.appHeader}>
            <View style={styles.brandMark}>
              <MoonStar color="#FFF8EA" size={28} strokeWidth={1.8} />
            </View>
            <View style={styles.headerText}>
              <Text style={styles.headerKicker}>Vedic problem solver</Text>
              <Text style={styles.appTitle}>Astro Solves</Text>
            </View>
            <Pressable accessibilityRole="button" testID="settings-button" style={[styles.iconButton, activeTab === "settings" && styles.iconButtonActive]} onPress={() => setActiveTab("settings")}>
              <Settings color="#FFF8EA" size={20} />
            </Pressable>
          </View>

          <LinearGradient colors={["#07030B", "#1A0B22", "#4B1732", "#083E4B", "#BA742C"]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.hero}>
            <View style={[styles.heroCorner, styles.heroCornerTopLeft]} />
            <View style={[styles.heroCorner, styles.heroCornerTopRight]} />
            <View style={[styles.heroCorner, styles.heroCornerBottomLeft]} />
            <View style={[styles.heroCorner, styles.heroCornerBottomRight]} />
            <View style={styles.heroTextWrap}>
              <View style={styles.heroRoyalKicker}>
                <View style={styles.royalNeedle} />
                <Text style={styles.heroRoyalText}>Jyotish Sabha</Text>
                <View style={styles.royalNeedle} />
              </View>
              <View style={styles.heroPills}>
                <Pill tone="gold">Shani</Pill>
                <Pill tone="green">Dasha</Pill>
                <Pill tone="ruby">Remedies</Pill>
              </View>
              <Text style={styles.heroHeadline}>{reading?.headline ?? "Find the pattern behind the problem."}</Text>
              <Text style={styles.heroCopy}>
                {reading?.summary ??
                  "A private Vedic guidance chamber for chart evidence, period readings, and one free remedy before any paid solution depth."}
              </Text>
              <View style={styles.heroMantraStrip}>
                <Text style={styles.heroMantra}>Om Shri Hanumate Namah</Text>
              </View>
            </View>
            <View style={styles.heroSidePanel}>
              <CosmicMap />
              <View style={styles.heroSignalGrid}>
                <Text style={styles.heroSignal}>Kundli</Text>
                <Text style={styles.heroSignal}>Shani</Text>
                <Text style={styles.heroSignal}>Remedy</Text>
              </View>
            </View>
          </LinearGradient>

          <View style={styles.statusBanner} testID="status-banner">
            <ShieldCheck color="#F3CB70" size={16} />
            <Text style={styles.statusBannerText}>{statusMessage}</Text>
          </View>

          <View style={styles.tabBar}>
            {tabOptions.map((tab) => {
              const active = activeTab === tab.key;
              return (
                <Pressable
                  key={tab.key}
                  accessibilityRole="button"
                  testID={`tab-${tab.key}`}
                  style={[styles.tabButton, active && styles.tabButtonActive]}
                  onPress={() => setActiveTab(tab.key)}
                >
                  {renderTabIcon(tab.key, active)}
                  <Text style={[styles.tabText, active && styles.tabTextActive]}>{tab.label}</Text>
                </Pressable>
              );
            })}
          </View>

          {activeTab === "profile" ? (
            <>
          <SectionHeader eyebrow="Profile" title="Birth Details" />
          <View style={styles.formCard}>
            <CardCrest title="Kundli Chamber" />
            <Field testID="field-full-name" label="Full name" value={profile.fullName} onChangeText={(fullName) => setProfile((prev) => ({ ...prev, fullName }))} />
            <View style={styles.row}>
              <View style={styles.half}>
                <Field testID="field-birth-date" label="Birth date" value={profile.birthDate} onChangeText={(birthDate) => setProfile((prev) => ({ ...prev, birthDate }))} />
              </View>
              <View style={styles.half}>
                <Field testID="field-birth-time" label="Birth time" value={profile.birthTime} onChangeText={(birthTime) => setProfile((prev) => ({ ...prev, birthTime }))} />
              </View>
            </View>
            <View style={styles.choiceRow}>
              {(["exact", "approximate", "unknown"] as BirthProfile["birthTimeConfidence"][]).map((choice) => (
                <Pressable
                  key={choice}
                  accessibilityRole="button"
                  testID={`birth-time-${choice}`}
                  style={[styles.choiceButton, profile.birthTimeConfidence === choice && styles.choiceButtonActive]}
                  onPress={() => setProfile((prev) => ({ ...prev, birthTimeConfidence: choice }))}
                >
                  <Text style={[styles.choiceText, profile.birthTimeConfidence === choice && styles.choiceTextActive]}>{choice}</Text>
                </Pressable>
              ))}
            </View>
            <Field testID="field-birthplace" label="Birthplace" value={placeQuery} onChangeText={setPlaceQuery} />
            <Pressable accessibilityRole="button" testID="search-place-button" style={styles.secondaryButton} onPress={searchBirthplace}>
              {placeLoading ? <ActivityIndicator color="#17111F" /> : <Search color="#17111F" size={18} />}
              <Text style={styles.secondaryButtonText}>Search place</Text>
            </Pressable>
            {placeResults.map((place) => (
              <Pressable key={place.id} accessibilityRole="button" testID={`place-result-${place.id}`} style={styles.placeResult} onPress={() => selectPlace(place)}>
                <MapPin color="#1C6B62" size={18} />
                <View style={styles.placeTextWrap}>
                  <Text style={styles.placeTitle}>{place.label}</Text>
                  <Text style={styles.placeMeta}>{place.timezone}</Text>
                </View>
              </Pressable>
            ))}
            <View style={styles.statusStrip}>
              <UserRound color="#1C6B62" size={16} />
              <Text style={styles.statusText}>{profile.birthplaceText} / {profile.timezone}</Text>
            </View>
            <View style={styles.consentGroup}>
              <ConsentToggle
                label="I accept privacy storage for my birth profile."
                value={profile.consent.privacyAccepted}
                onValueChange={(privacyAccepted) =>
                  setProfile((prev) => ({
                    ...prev,
                    consent: { ...prev.consent, privacyAccepted }
                  }))
                }
              />
              <ConsentToggle
                label="Save my shared context to make future readings more personal."
                value={profile.consent.aiPersonalization}
                onValueChange={(aiPersonalization) =>
                  setProfile((prev) => ({
                    ...prev,
                    consent: { ...prev.consent, aiPersonalization }
                  }))
                }
              />
              <View style={styles.memoryNote}>
                <ShieldCheck color="#CBA45A" size={16} />
                <Text style={styles.memoryNoteText}>Pattern memory stays tied to this profile and is cleared when you delete account data.</Text>
              </View>
            </View>
            <Pressable accessibilityRole="button" testID="save-profile-button" style={[styles.primaryButton, !canSubmit && styles.disabledButton]} onPress={saveProfile} disabled={profileLoading}>
              {profileLoading ? <ActivityIndicator color="#FFF8EA" /> : <CalendarDays color="#FFF8EA" size={20} />}
              <Text style={styles.primaryButtonText}>{profileSaved ? "Refresh chart" : "Save profile"}</Text>
            </Pressable>
          </View>
            </>
          ) : null}

          {activeTab === "readings" ? (
            <>
          {chart ? (
            <>
              <SectionHeader eyebrow="Receipts" title="Chart Snapshot" />
              <View style={styles.metricsGrid}>
                <Metric label="Ascendant" value={`${chart.ascendant.sign} ${chart.ascendant.degree.toFixed(1)}`} />
                <Metric label="Moon" value={`${chart.moon.sign} / ${chart.moon.nakshatra}`} />
                <Metric label="Dasha" value={`${chart.dasha.mahadasha}-${chart.dasha.antardasha}`} />
                <Metric label="Saturn" value={saturnTransitLabel(chart)} />
                <Metric label="Life path" value={`${chart.numerology.lifePathNumber}`} />
                <Metric label="Engine" value={chart.calculationEngine.split("+")[0]?.trim() ?? chart.calculationEngine} />
              </View>
            </>
          ) : null}

          <SectionHeader eyebrow="Reading" title="Period Guidance" />
          <EntitlementPanel label="Today's free reading" status={entitlements?.reading} />
          <View style={styles.segment}>
            {periodOptions.map((period) => (
              <Pressable
                key={period.key}
                accessibilityRole="button"
                testID={`period-${period.key}`}
                style={[styles.segmentButton, activePeriod === period.key && styles.segmentButtonActive]}
                onPress={() => selectReadingPeriod(period.key)}
              >
                <Text style={[styles.segmentText, activePeriod === period.key && styles.segmentTextActive]}>{period.label}</Text>
              </Pressable>
            ))}
          </View>
          <Pressable accessibilityRole="button" testID="unlock-reading-button" style={styles.primaryButton} onPress={unlockPeriodReading} disabled={readingLoading}>
            {readingLoading ? <ActivityIndicator color="#FFF8EA" /> : <Sparkles color="#FFF8EA" size={20} />}
            <Text style={styles.primaryButtonText}>Open {titleCasePeriod(activePeriod)} Reading</Text>
          </Pressable>

          {readingLoading ? (
            <View style={styles.loadingCard}>
              <ActivityIndicator color="#B85A2E" />
            </View>
          ) : reading ? (
            <>
              <ReadingLane title="Love" body={reading.love} />
              <ReadingLane title="Career" body={reading.career} />
              <ReadingLane title="Money" body={reading.money} />
              <ReadingLane title="Mind" body={reading.mind} />
              <View style={styles.actionGrid}>
                {reading.doActions.map((item) => (
                  <Pill key={`do-${item}`} tone="green">Do: {item}</Pill>
                ))}
                {reading.dontActions.map((item) => (
                  <Pill key={`dont-${item}`} tone="ruby">Avoid: {item}</Pill>
                ))}
              </View>
              <View style={styles.evidenceCard}>
                <View style={styles.evidenceHeader}>
                  <ShieldCheck color="#1C6B62" size={18} />
                  <Text style={styles.evidenceTitle}>Astro Evidence</Text>
                </View>
                {reading.astroEvidence.map((item) => (
                  <Text style={styles.evidenceText} key={item}>{item}</Text>
                ))}
              </View>
            </>
          ) : (
            <View style={styles.emptyCard}>
              <Sparkles color="#B85A2E" size={20} />
              <Text style={styles.emptyText}>{profileSaved ? "Choose and open today's free reading." : "Save your profile to open the first reading."}</Text>
            </View>
          )}
            </>
          ) : null}

          {activeTab === "harmony" ? (
            <>
              <SectionHeader eyebrow="Harmony" title="Match & Peace" />
              <View style={styles.formCard}>
                <CardCrest title="Relationship Chamber" />
                <Field testID="field-partner-name" label="Partner name" value={partnerName} onChangeText={setPartnerName} />
                <Field testID="field-partner-birth-date" label="Partner birth date" value={partnerBirthDate} onChangeText={setPartnerBirthDate} placeholder="YYYY-MM-DD" />
                <View style={styles.choiceRow}>
                  {(["relationship", "marriage", "peace"] as RelationshipFocus[]).map((focus) => (
                    <Pressable
                      key={focus}
                      accessibilityRole="button"
                      testID={`harmony-focus-${focus}`}
                      style={[styles.choiceButton, relationshipFocus === focus && styles.choiceButtonActive]}
                      onPress={() => setRelationshipFocus(focus)}
                    >
                      <Text style={[styles.choiceText, relationshipFocus === focus && styles.choiceTextActive]}>{focus}</Text>
                    </Pressable>
                  ))}
                </View>
                <Pressable accessibilityRole="button" testID="generate-harmony-button" style={styles.primaryButton} onPress={generateHarmony} disabled={harmonyLoading}>
                  {harmonyLoading ? <ActivityIndicator color="#FFF8EA" /> : <HeartHandshake color="#FFF8EA" size={20} />}
                  <Text style={styles.primaryButtonText}>Build Harmony Map</Text>
                </Pressable>
              </View>

              {harmonyLoading ? (
                <View style={styles.loadingCard}>
                  <ActivityIndicator color="#B85A2E" />
                </View>
              ) : harmonyInsight ? (
                <>
                  <View style={styles.harmonyScoreCard}>
                    <Text style={styles.harmonyScore}>{harmonyInsight.compatibilityScore}%</Text>
                    <Text style={styles.harmonyScoreLabel}>{harmonyInsight.title}</Text>
                  </View>
                  <View style={styles.metricsGrid}>
                    <Metric label="Your sign" value={harmonyInsight.user.sign} />
                    <Metric label="Partner sign" value={harmonyInsight.partner.sign} />
                    <Metric label="Your numbers" value={`${harmonyInsight.user.birthNumber}/${harmonyInsight.user.lifePathNumber}/${harmonyInsight.user.nameNumber}`} />
                    <Metric label="Partner nums" value={`${harmonyInsight.partner.birthNumber ?? "-"} / ${harmonyInsight.partner.lifePathNumber ?? "-"} / ${harmonyInsight.partner.nameNumber}`} />
                  </View>
                  <ReadingLane title="Relationship" body={harmonyInsight.relationshipLens} />
                  <ReadingLane title="Marriage" body={harmonyInsight.marriageLens} />
                  <ReadingLane title="Numerology" body={harmonyInsight.numerologyLens} />
                  <ReadingLane title="Peace Practice" body={harmonyInsight.peacePractice} />
                  <View style={styles.evidenceCard}>
                    <View style={styles.evidenceHeader}>
                      <HeartHandshake color="#1C6B62" size={18} />
                      <Text style={styles.evidenceTitle}>Best Matches</Text>
                    </View>
                    {harmonyInsight.bestRelationshipMatches.map((item) => (
                      <Text style={styles.evidenceText} key={`relationship-${item}`}>{item}</Text>
                    ))}
                    <Text style={styles.insightLabel}>Marriage stability</Text>
                    {harmonyInsight.bestMarriageMatches.map((item) => (
                      <Text style={styles.evidenceText} key={`marriage-${item}`}>{item}</Text>
                    ))}
                  </View>
                  <View style={styles.watchoutCard}>
                    {harmonyInsight.watchouts.map((item) => (
                      <View style={styles.watchoutRow} key={item}>
                        <Sparkles color="#B85A2E" size={14} />
                        <Text style={styles.watchoutText}>{item}</Text>
                      </View>
                    ))}
                  </View>
                  <View style={styles.evidenceCard}>
                    <View style={styles.evidenceHeader}>
                      <Hash color="#1C6B62" size={18} />
                      <Text style={styles.evidenceTitle}>Harmony Evidence</Text>
                    </View>
                    {harmonyInsight.astroEvidence.map((item) => (
                      <Text style={styles.evidenceText} key={item}>{item}</Text>
                    ))}
                  </View>
                </>
              ) : (
                <View style={styles.emptyCard}>
                  <HeartHandshake color="#B85A2E" size={20} />
                  <Text style={styles.emptyText}>Add partner details to see match, numerology, and peace guidance.</Text>
                </View>
              )}
            </>
          ) : null}

          {activeTab === "problems" ? (
            <>
          <SectionHeader eyebrow="Problem Solver" title="Share The Issue" />
          <EntitlementPanel label="Free problem analyses" status={entitlements?.problem} />
          <View style={styles.formCard}>
            <CardCrest title="Confidential Sabha" />
            <View style={styles.categoryGrid}>
              {categories.map((category) => (
                <Pressable
                  key={category.key}
                  accessibilityRole="button"
                  testID={`category-${category.key}`}
                  style={[styles.categoryChip, problemCategory === category.key && styles.categoryChipActive]}
                  onPress={() => setProblemCategory(category.key)}
                >
                  <Text style={[styles.categoryText, problemCategory === category.key && styles.categoryTextActive]}>{category.label}</Text>
                </Pressable>
              ))}
            </View>
            <Field
              testID="field-problem-details"
              label="Problem details"
              value={problemDetails}
              onChangeText={setProblemDetails}
              multiline
              placeholder="Delays, fear, relationship tension, family pressure, money stress..."
            />
            <Pressable accessibilityRole="button" testID="analyze-problem-button" style={styles.primaryButton} onPress={analyzeProblem} disabled={problemLoading}>
              {problemLoading ? <ActivityIndicator color="#FFF8EA" /> : <MessageCircle color="#FFF8EA" size={20} />}
              <Text style={styles.primaryButtonText}>Analyze problem</Text>
            </Pressable>
          </View>

          {problemInsight ? (
            <>
              <View style={styles.insightCard}>
                <Text style={styles.problemTitle}>{problemInsight.problemTitle}</Text>
                <Text style={styles.bodyText}>{problemInsight.reassurance}</Text>
                <Text style={styles.insightLabel}>Astrological lens</Text>
                <Text style={styles.bodyText}>{problemInsight.astroPattern}</Text>
                <Text style={styles.insightLabel}>Timeline</Text>
                <Text style={styles.bodyText}>{problemInsight.timeline}</Text>
              </View>
              <View style={styles.watchoutCard}>
                {problemInsight.watchouts.map((item) => (
                  <View style={styles.watchoutRow} key={item}>
                    <Sparkles color="#B85A2E" size={14} />
                    <Text style={styles.watchoutText}>{item}</Text>
                  </View>
                ))}
              </View>
              <SolutionCard step={problemInsight.freeSolution} locked={false} />
              {problemInsight.premiumSolutions.map((step) => (
                <SolutionCard key={step.title} step={step} locked={!solutionUnlocked} />
              ))}
              <Pressable accessibilityRole="button" testID="unlock-solutions-button" style={[styles.unlockButton, solutionUnlocked && styles.unlockedButton]} onPress={unlockSolutions} disabled={solutionLoading || solutionUnlocked}>
                {solutionLoading ? <ActivityIndicator color="#FFF8EA" /> : <Crown color="#FFF8EA" size={20} />}
                <Text style={styles.unlockButtonText}>{solutionUnlocked ? (freeProblemSolutionOpen ? "Free solution paths open" : "Solution pack unlocked") : "Unlock solution pack"}</Text>
              </Pressable>
              <View style={styles.evidenceCard}>
                <View style={styles.evidenceHeader}>
                  <ShieldCheck color="#1C6B62" size={18} />
                  <Text style={styles.evidenceTitle}>Problem Evidence</Text>
                </View>
                {problemInsight.astroEvidence.map((item) => (
                  <Text style={styles.evidenceText} key={item}>{item}</Text>
                ))}
              </View>
            </>
          ) : null}
            </>
          ) : null}

          {activeTab === "premium" ? (
            <>
              <SectionHeader eyebrow="Royal Plan" title="Royal Depth" />
              <View style={styles.premiumIntro}>
                <Crown color="#F3CB70" size={20} />
                <Text style={styles.premiumIntroText}>Go deeper only when the issue needs a longer map, a steadier practice, or extra period guidance.</Text>
              </View>
              <View style={styles.paidIdeaGrid}>
                {paidIdeas.map((idea) => {
                  const active = selectedPaidIdea === idea.title;
                  return (
                    <Pressable
                      key={idea.title}
                      accessibilityRole="button"
                      testID={`paid-idea-${idea.title.toLowerCase().replaceAll(" ", "-")}`}
                      style={[styles.paidIdeaCard, active && styles.paidIdeaCardActive]}
                      onPress={() => {
                        setSelectedPaidIdea(idea.title);
                        setStatusMessage(`${idea.title} saved for the Royal plan preview.`);
                      }}
                    >
                      <Text style={[styles.paidIdeaTitle, active && styles.paidIdeaTitleActive]}>{idea.title}</Text>
                      <Text style={[styles.paidIdeaBody, active && styles.paidIdeaBodyActive]}>{idea.body}</Text>
                    </Pressable>
                  );
                })}
              </View>
            </>
          ) : null}

          {activeTab === "settings" ? (
            <>
              <SectionHeader eyebrow="Settings" title="Account & Data" />
              <View style={styles.evidenceCard}>
                <View style={styles.evidenceHeader}>
                  <UserRound color="#1C6B62" size={18} />
                  <Text style={styles.evidenceTitle}>Profile</Text>
                </View>
                <Text style={styles.evidenceText}>{profile.fullName || "Name pending"}</Text>
                <Text style={styles.evidenceText}>{profile.birthDate} at {profile.birthTime} / {profile.birthplaceText}</Text>
                <Text style={styles.evidenceText}>Birth time confidence: {profile.birthTimeConfidence}</Text>
              </View>
              <View style={styles.evidenceCard}>
                <View style={styles.evidenceHeader}>
                  <Hash color="#1C6B62" size={18} />
                  <Text style={styles.evidenceTitle}>User Data</Text>
                </View>
                <Text style={styles.evidenceText}>Problem memories: {memoryContext?.problemCount ?? 0}</Text>
                <Text style={styles.evidenceText}>Reading unlock: {entitlements?.reading.message ?? "Save profile to begin."}</Text>
                <Text style={styles.evidenceText}>Problem access: {entitlements?.problem.message ?? "Save profile to begin."}</Text>
                {Object.entries(memoryContext?.categoryCounts ?? {}).slice(0, 4).map(([category, count]) => (
                  <Text style={styles.evidenceText} key={category}>{category}: {count}</Text>
                ))}
              </View>
              <View style={styles.formCard}>
                <CardCrest title="Privacy Controls" />
                <ConsentToggle
                  label="I accept privacy storage for my birth profile."
                  value={profile.consent.privacyAccepted}
                  onValueChange={(privacyAccepted) =>
                    setProfile((prev) => ({
                      ...prev,
                      consent: { ...prev.consent, privacyAccepted }
                    }))
                  }
                />
                <ConsentToggle
                  label="Save my shared context to make future readings more personal."
                  value={profile.consent.aiPersonalization}
                  onValueChange={(aiPersonalization) =>
                    setProfile((prev) => ({
                      ...prev,
                      consent: { ...prev.consent, aiPersonalization }
                    }))
                  }
                />
                <ConsentToggle
                  label="Send me product and ritual reminders."
                  value={profile.consent.marketingOptIn}
                  onValueChange={(marketingOptIn) =>
                    setProfile((prev) => ({
                      ...prev,
                      consent: { ...prev.consent, marketingOptIn }
                    }))
                  }
                />
                <Pressable accessibilityRole="button" testID="save-settings-button" style={styles.primaryButton} onPress={saveSettings} disabled={profileLoading}>
                  {profileLoading ? <ActivityIndicator color="#FFF8EA" /> : <ShieldCheck color="#FFF8EA" size={20} />}
                  <Text style={styles.primaryButtonText}>Save Settings</Text>
                </Pressable>
              </View>
              <Pressable accessibilityRole="button" testID="edit-profile-button" style={styles.secondaryButton} onPress={() => setActiveTab("profile")}>
                <UserRound color="#17111F" size={18} />
                <Text style={styles.secondaryButtonText}>Edit birth profile</Text>
              </Pressable>
              <Pressable accessibilityRole="button" testID="notify-button" style={styles.secondaryButton} onPress={scheduleDailyPing}>
                <Bell color="#17111F" size={18} />
                <Text style={styles.secondaryButtonText}>Set daily reminder</Text>
              </Pressable>
              <Pressable accessibilityRole="button" testID="delete-account-button" style={styles.deleteButton} onPress={deleteAccount}>
                <Trash2 color="#8D2F23" size={18} />
                <Text style={styles.deleteText}>Delete account data</Text>
              </Pressable>
            </>
          ) : null}

          <Text style={styles.disclaimer}>
            {problemInsight?.safetyDisclaimer ?? reading?.safetyDisclaimer ??
              "Astrology is reflective spiritual guidance, not medical, legal, financial, or crisis advice. Remedies are devotional and behavioral supports, not guaranteed fixes."}
          </Text>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: "#120A17"
  },
  screen: {
    flex: 1
  },
  content: {
    width: "100%",
    maxWidth: 520,
    alignSelf: "center",
    padding: 18,
    gap: 16,
    backgroundColor: "#120A17"
  },
  appHeader: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    paddingTop: 8,
    paddingBottom: 4
  },
  brandMark: {
    width: 52,
    height: 52,
    borderRadius: 8,
    backgroundColor: "#211327",
    borderWidth: 1,
    borderColor: "#CBA45A",
    alignItems: "center",
    justifyContent: "center"
  },
  headerText: {
    flex: 1
  },
  headerKicker: {
    color: "#CBA45A",
    fontSize: 12,
    fontWeight: "800",
    letterSpacing: 0,
    textTransform: "uppercase"
  },
  appTitle: {
    color: "#FFF7E8",
    fontSize: 34,
    lineHeight: 38,
    fontWeight: "900",
    letterSpacing: 0
  },
  iconButton: {
    width: 44,
    height: 44,
    borderRadius: 8,
    backgroundColor: "#315A51",
    borderWidth: 1,
    borderColor: "#CBA45A",
    alignItems: "center",
    justifyContent: "center"
  },
  iconButtonActive: {
    backgroundColor: "#8D3D28"
  },
  hero: {
    borderRadius: 8,
    minHeight: 250,
    padding: 22,
    gap: 18,
    overflow: "hidden",
    borderWidth: 1,
    borderColor: "#E4C16A",
    flexDirection: "row",
    flexWrap: "wrap",
    alignItems: "center",
    justifyContent: "space-between",
    shadowColor: "#000000",
    shadowOpacity: 0.42,
    shadowRadius: 24,
    shadowOffset: { width: 0, height: 16 },
    elevation: 9
  },
  heroCorner: {
    position: "absolute",
    width: 36,
    height: 36,
    borderColor: "rgba(255, 231, 172, 0.82)"
  },
  heroCornerTopLeft: {
    top: 12,
    left: 12,
    borderTopWidth: 1,
    borderLeftWidth: 1
  },
  heroCornerTopRight: {
    top: 12,
    right: 12,
    borderTopWidth: 1,
    borderRightWidth: 1
  },
  heroCornerBottomLeft: {
    bottom: 12,
    left: 12,
    borderBottomWidth: 1,
    borderLeftWidth: 1
  },
  heroCornerBottomRight: {
    bottom: 12,
    right: 12,
    borderBottomWidth: 1,
    borderRightWidth: 1
  },
  heroTextWrap: {
    flex: 1,
    minWidth: 280,
    gap: 12
  },
  heroRoyalKicker: {
    flexDirection: "row",
    alignItems: "center",
    alignSelf: "flex-start",
    gap: 8
  },
  royalNeedle: {
    width: 34,
    height: 1,
    backgroundColor: "#E7C16A"
  },
  heroRoyalText: {
    color: "#FFE7AC",
    fontSize: 12,
    fontWeight: "900",
    letterSpacing: 0,
    textTransform: "uppercase"
  },
  heroPills: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8
  },
  heroHeadline: {
    color: "#FFF8EA",
    fontSize: 34,
    lineHeight: 40,
    fontWeight: "900",
    letterSpacing: 0
  },
  heroCopy: {
    color: "#F2D9B3",
    fontSize: 15,
    lineHeight: 22,
    fontWeight: "700"
  },
  heroMantraStrip: {
    alignSelf: "flex-start",
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "rgba(255, 231, 172, 0.5)",
    backgroundColor: "rgba(7, 3, 11, 0.46)",
    paddingHorizontal: 10,
    paddingVertical: 7
  },
  heroMantra: {
    color: "#FFF1C8",
    fontSize: 12,
    lineHeight: 16,
    fontWeight: "900"
  },
  heroSidePanel: {
    minWidth: 158,
    alignItems: "center",
    gap: 10
  },
  heroSignalGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    justifyContent: "center",
    gap: 6,
    maxWidth: 166
  },
  heroSignal: {
    color: "#FFF1C8",
    fontSize: 11,
    fontWeight: "900",
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "rgba(255, 231, 172, 0.42)",
    backgroundColor: "rgba(7, 3, 11, 0.45)",
    paddingHorizontal: 8,
    paddingVertical: 5,
    overflow: "hidden"
  },
  cosmicMap: {
    width: 138,
    height: 138,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "rgba(255, 231, 172, 0.72)",
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "rgba(18, 10, 23, 0.6)"
  },
  cosmicPlate: {
    position: "absolute",
    width: 124,
    height: 124,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "rgba(255, 231, 172, 0.3)",
    backgroundColor: "rgba(8, 62, 75, 0.18)",
    transform: [{ rotate: "45deg" }]
  },
  orbitOuter: {
    position: "absolute",
    width: 116,
    height: 116,
    borderRadius: 58,
    borderWidth: 1,
    borderColor: "rgba(245, 183, 81, 0.6)"
  },
  orbitMiddle: {
    position: "absolute",
    width: 86,
    height: 86,
    borderRadius: 43,
    borderWidth: 1,
    borderColor: "rgba(101, 180, 164, 0.7)"
  },
  orbitInner: {
    position: "absolute",
    width: 54,
    height: 54,
    borderRadius: 27,
    borderWidth: 1,
    borderColor: "rgba(255, 248, 234, 0.55)"
  },
  starDot: {
    position: "absolute",
    width: 7,
    height: 7,
    borderRadius: 4,
    backgroundColor: "#F5B751"
  },
  starOne: {
    top: 17,
    left: 35
  },
  starTwo: {
    top: 36,
    right: 20,
    backgroundColor: "#65B4A4"
  },
  starThree: {
    bottom: 22,
    left: 25,
    backgroundColor: "#D36A3A"
  },
  starFour: {
    bottom: 30,
    right: 35,
    backgroundColor: "#FFF8EA"
  },
  statusBanner: {
    minHeight: 44,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#CBA45A",
    backgroundColor: "#211327",
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    paddingHorizontal: 12,
    paddingVertical: 10
  },
  statusBannerText: {
    flex: 1,
    color: "#FFF1C8",
    fontSize: 13,
    lineHeight: 18,
    fontWeight: "800"
  },
  tabBar: {
    minHeight: 66,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#CBA45A",
    backgroundColor: "#211327",
    flexDirection: "row",
    padding: 5,
    gap: 5
  },
  tabButton: {
    flex: 1,
    minHeight: 54,
    borderRadius: 8,
    alignItems: "center",
    justifyContent: "center",
    gap: 4,
    paddingHorizontal: 2
  },
  tabButtonActive: {
    backgroundColor: "#8D3D28",
    borderWidth: 1,
    borderColor: "#F3CB70"
  },
  tabText: {
    color: "#D8BA75",
    fontSize: 11,
    fontWeight: "900"
  },
  tabTextActive: {
    color: "#FFF8EA"
  },
  entitlementPanel: {
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#E0BA62",
    backgroundColor: "#FFF3DA",
    padding: 13,
    gap: 8
  },
  entitlementTop: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 10
  },
  entitlementLabel: {
    color: "#6E4324",
    fontSize: 13,
    fontWeight: "900",
    textTransform: "uppercase"
  },
  entitlementCount: {
    color: "#17111F",
    fontSize: 18,
    lineHeight: 22,
    fontWeight: "900"
  },
  entitlementMessage: {
    color: "#5A5046",
    fontSize: 13,
    lineHeight: 18,
    fontWeight: "800"
  },
  entitlementTrack: {
    height: 7,
    borderRadius: 7,
    overflow: "hidden",
    backgroundColor: "#E1CFAD"
  },
  entitlementFill: {
    height: "100%",
    borderRadius: 7,
    backgroundColor: "#8D3D28"
  },
  sectionHeader: {
    gap: 3,
    marginTop: 4
  },
  kicker: {
    color: "#CBA45A",
    fontSize: 12,
    fontWeight: "900",
    letterSpacing: 0,
    textTransform: "uppercase"
  },
  sectionTitle: {
    color: "#FFF7E8",
    fontSize: 22,
    lineHeight: 27,
    fontWeight: "900",
    letterSpacing: 0
  },
  formCard: {
    borderRadius: 8,
    backgroundColor: "#FFF7E8",
    borderWidth: 1,
    borderColor: "#E0BA62",
    padding: 15,
    gap: 12,
    shadowColor: "#000000",
    shadowOpacity: 0.2,
    shadowRadius: 18,
    shadowOffset: { width: 0, height: 10 },
    elevation: 5
  },
  cardCrest: {
    minHeight: 30,
    flexDirection: "row",
    alignItems: "center",
    gap: 9,
    marginBottom: 1
  },
  crestGem: {
    width: 11,
    height: 11,
    borderRadius: 2,
    borderWidth: 1,
    borderColor: "#D6B56B",
    backgroundColor: "#9E123E",
    transform: [{ rotate: "45deg" }]
  },
  cardCrestText: {
    color: "#6E4324",
    fontSize: 12,
    fontWeight: "900",
    letterSpacing: 0,
    textTransform: "uppercase"
  },
  crestLine: {
    flex: 1,
    height: 1,
    backgroundColor: "#D6B56B"
  },
  field: {
    gap: 6
  },
  label: {
    color: "#5D5144",
    fontSize: 13,
    fontWeight: "800"
  },
  input: {
    minHeight: 46,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#D6C4A8",
    backgroundColor: "#FBF5EA",
    color: "#17111F",
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 16
  },
  textArea: {
    minHeight: 124,
    lineHeight: 22
  },
  row: {
    flexDirection: "row",
    gap: 10
  },
  half: {
    flex: 1,
    minWidth: 0
  },
  choiceRow: {
    flexDirection: "row",
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#2D594F",
    overflow: "hidden"
  },
  choiceButton: {
    flex: 1,
    minHeight: 42,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#FFF8EA",
    paddingHorizontal: 4
  },
  choiceButtonActive: {
    backgroundColor: "#2D594F"
  },
  choiceText: {
    color: "#2D594F",
    fontSize: 12,
    fontWeight: "900",
    textTransform: "capitalize"
  },
  choiceTextActive: {
    color: "#FFF8EA"
  },
  secondaryButton: {
    minHeight: 48,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#B88C3B",
    backgroundColor: "#F3CB70",
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    paddingHorizontal: 12
  },
  secondaryButtonText: {
    color: "#17111F",
    fontSize: 15,
    fontWeight: "900"
  },
  placeResult: {
    flexDirection: "row",
    gap: 10,
    alignItems: "center",
    minHeight: 58,
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderRadius: 8,
    backgroundColor: "#F6EFE2",
    borderWidth: 1,
    borderColor: "#D6C4A8"
  },
  placeTextWrap: {
    flex: 1,
    gap: 2
  },
  placeTitle: {
    color: "#17111F",
    fontSize: 14,
    lineHeight: 19,
    fontWeight: "900"
  },
  placeMeta: {
    color: "#6A6258",
    fontSize: 12,
    fontWeight: "800"
  },
  statusStrip: {
    minHeight: 42,
    borderRadius: 8,
    backgroundColor: "#E5F0EA",
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    paddingHorizontal: 10
  },
  statusText: {
    flex: 1,
    color: "#1C4E46",
    fontSize: 13,
    fontWeight: "800"
  },
  consentGroup: {
    gap: 10
  },
  memoryNote: {
    minHeight: 42,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#D6B56B",
    backgroundColor: "#221528",
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    paddingHorizontal: 10,
    paddingVertical: 9
  },
  memoryNoteText: {
    flex: 1,
    color: "#F3D7A4",
    fontSize: 12,
    lineHeight: 17,
    fontWeight: "800"
  },
  toggleRow: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 10
  },
  checkbox: {
    width: 22,
    height: 22,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: "#2D594F",
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#FFF8EA",
    marginTop: 1
  },
  checkboxActive: {
    backgroundColor: "#2D594F",
    borderColor: "#2D594F"
  },
  toggleLabel: {
    flex: 1,
    color: "#332D28",
    fontSize: 13,
    lineHeight: 18,
    fontWeight: "800"
  },
  primaryButton: {
    minHeight: 50,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#D6B56B",
    backgroundColor: "#211327",
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    paddingHorizontal: 12
  },
  disabledButton: {
    opacity: 0.45
  },
  primaryButtonText: {
    color: "#FFF8EA",
    fontSize: 16,
    fontWeight: "900"
  },
  metricsGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10
  },
  metricCard: {
    width: "48%",
    minHeight: 76,
    borderRadius: 8,
    backgroundColor: "#FFF3DA",
    borderWidth: 1,
    borderColor: "#E0BA62",
    padding: 12,
    gap: 6
  },
  metricLabel: {
    color: "#7A6040",
    fontSize: 11,
    fontWeight: "900",
    textTransform: "uppercase",
    letterSpacing: 0
  },
  metricValue: {
    color: "#17111F",
    fontSize: 15,
    lineHeight: 20,
    fontWeight: "900"
  },
  segment: {
    flexDirection: "row",
    borderRadius: 8,
    borderWidth: 1,
    overflow: "hidden",
    backgroundColor: "#FFF3DA",
    borderColor: "#E0BA62"
  },
  segmentButton: {
    flex: 1,
    minHeight: 46,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 4
  },
  segmentButtonActive: {
    backgroundColor: "#211327"
  },
  segmentText: {
    color: "#17111F",
    fontSize: 13,
    fontWeight: "900"
  },
  segmentTextActive: {
    color: "#FFF8EA"
  },
  loadingCard: {
    minHeight: 100,
    borderRadius: 8,
    backgroundColor: "#FFF7E8",
    borderWidth: 1,
    borderColor: "#E4D4B8",
    alignItems: "center",
    justifyContent: "center"
  },
  harmonyScoreCard: {
    minHeight: 118,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#F3CB70",
    backgroundColor: "#211327",
    padding: 16,
    gap: 8,
    alignItems: "center",
    justifyContent: "center"
  },
  harmonyScore: {
    color: "#FFF8EA",
    fontSize: 42,
    lineHeight: 48,
    fontWeight: "900",
    letterSpacing: 0
  },
  harmonyScoreLabel: {
    color: "#F3D7A4",
    fontSize: 14,
    lineHeight: 20,
    fontWeight: "800",
    textAlign: "center"
  },
  readingLane: {
    borderRadius: 8,
    backgroundColor: "#FFF3DA",
    borderWidth: 1,
    borderColor: "#E0BA62",
    padding: 14,
    gap: 8
  },
  laneTitle: {
    color: "#8D3D28",
    fontSize: 13,
    fontWeight: "900",
    textTransform: "uppercase",
    letterSpacing: 0
  },
  bodyText: {
    color: "#332D28",
    fontSize: 15,
    lineHeight: 22,
    fontWeight: "600"
  },
  actionGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8
  },
  pill: {
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 7,
    maxWidth: "100%"
  },
  greenPill: {
    backgroundColor: "#DDEDE6"
  },
  goldPill: {
    backgroundColor: "#F3CB70"
  },
  rubyPill: {
    backgroundColor: "#F2D5CD"
  },
  inkPill: {
    backgroundColor: "#17111F"
  },
  pillText: {
    color: "#243F37",
    fontSize: 12,
    fontWeight: "900"
  },
  inkPillText: {
    color: "#FFF8EA"
  },
  evidenceCard: {
    borderRadius: 8,
    backgroundColor: "#FBF0DD",
    borderWidth: 1,
    borderColor: "#D6B56B",
    padding: 13,
    gap: 8
  },
  evidenceHeader: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8
  },
  evidenceTitle: {
    color: "#1C4E46",
    fontSize: 13,
    fontWeight: "900",
    textTransform: "uppercase",
    letterSpacing: 0
  },
  evidenceText: {
    color: "#5A5046",
    fontSize: 13,
    lineHeight: 19,
    fontWeight: "700"
  },
  emptyCard: {
    minHeight: 92,
    borderRadius: 8,
    backgroundColor: "#FFF7E8",
    borderWidth: 1,
    borderColor: "#E4D4B8",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    padding: 14
  },
  emptyText: {
    color: "#5A5046",
    fontSize: 14,
    fontWeight: "800",
    textAlign: "center"
  },
  categoryGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8
  },
  categoryChip: {
    minHeight: 38,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#C7B08E",
    backgroundColor: "#FBF5EA",
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 11
  },
  categoryChipActive: {
    backgroundColor: "#B85A2E",
    borderColor: "#B85A2E"
  },
  categoryText: {
    color: "#5B4936",
    fontSize: 13,
    fontWeight: "900"
  },
  categoryTextActive: {
    color: "#FFF8EA"
  },
  insightCard: {
    borderRadius: 8,
    backgroundColor: "#FFF7E8",
    borderWidth: 1,
    borderColor: "#D6B56B",
    padding: 14,
    gap: 10
  },
  problemTitle: {
    color: "#17111F",
    fontSize: 20,
    lineHeight: 25,
    fontWeight: "900",
    letterSpacing: 0
  },
  insightLabel: {
    color: "#8D5A2D",
    fontSize: 12,
    fontWeight: "900",
    textTransform: "uppercase",
    letterSpacing: 0,
    marginTop: 4
  },
  watchoutCard: {
    borderRadius: 8,
    backgroundColor: "#F3E5D6",
    borderWidth: 1,
    borderColor: "#DDBB96",
    padding: 13,
    gap: 10
  },
  watchoutRow: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 8
  },
  watchoutText: {
    flex: 1,
    color: "#4A3929",
    fontSize: 14,
    lineHeight: 20,
    fontWeight: "800"
  },
  solutionCard: {
    borderRadius: 8,
    backgroundColor: "#FFF7E8",
    borderWidth: 1,
    borderColor: "#D6B56B",
    padding: 14,
    gap: 10
  },
  lockedSolutionCard: {
    backgroundColor: "#F8F0E4",
    borderColor: "#C7B08E"
  },
  solutionHeader: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10
  },
  solutionIcon: {
    width: 36,
    height: 36,
    borderRadius: 8,
    alignItems: "center",
    justifyContent: "center"
  },
  freeIcon: {
    backgroundColor: "#F3CB70"
  },
  lockedIcon: {
    backgroundColor: "#17111F"
  },
  solutionTitleWrap: {
    flex: 1,
    gap: 2
  },
  solutionTitle: {
    color: "#17111F",
    fontSize: 16,
    lineHeight: 21,
    fontWeight: "900"
  },
  solutionMeta: {
    color: "#7A6040",
    fontSize: 12,
    fontWeight: "900"
  },
  solutionWhy: {
    color: "#735E49",
    fontSize: 13,
    lineHeight: 19,
    fontWeight: "800"
  },
  unlockButton: {
    minHeight: 52,
    borderRadius: 8,
    backgroundColor: "#B85A2E",
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    paddingHorizontal: 12
  },
  unlockedButton: {
    backgroundColor: "#2D594F"
  },
  unlockButtonText: {
    color: "#FFF8EA",
    fontSize: 16,
    fontWeight: "900"
  },
  premiumIntro: {
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#CBA45A",
    backgroundColor: "#211327",
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    padding: 13
  },
  premiumIntroText: {
    flex: 1,
    color: "#FFF1C8",
    fontSize: 13,
    lineHeight: 19,
    fontWeight: "800"
  },
  paidIdeaGrid: {
    gap: 10
  },
  paidIdeaCard: {
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#D6B56B",
    backgroundColor: "#FFF7E8",
    padding: 14,
    gap: 7
  },
  paidIdeaCardActive: {
    backgroundColor: "#1F3F3B",
    borderColor: "#F3CB70"
  },
  paidIdeaTitle: {
    color: "#17111F",
    fontSize: 16,
    lineHeight: 21,
    fontWeight: "900"
  },
  paidIdeaTitleActive: {
    color: "#FFF8EA"
  },
  paidIdeaBody: {
    color: "#5A5046",
    fontSize: 13,
    lineHeight: 19,
    fontWeight: "800"
  },
  paidIdeaBodyActive: {
    color: "#F2D9B3"
  },
  deleteButton: {
    minHeight: 44,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#CFA49B",
    backgroundColor: "#FFF2EF",
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    marginTop: 6
  },
  deleteText: {
    color: "#8D2F23",
    fontSize: 14,
    fontWeight: "900"
  },
  disclaimer: {
    color: "#6B5D4E",
    fontSize: 12,
    lineHeight: 18,
    paddingBottom: 24,
    fontWeight: "700"
  }
});
