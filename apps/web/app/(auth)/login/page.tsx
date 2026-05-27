import { AuthForm } from "@/features/auth/components/auth-form";

export default function LoginPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-[#08090a] px-6 py-10 text-white">
      <AuthForm mode="login" />
    </main>
  );
}
