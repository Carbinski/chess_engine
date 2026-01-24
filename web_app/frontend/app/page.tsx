import ChessGame from "@/components/ChessGame";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-8 bg-gray-900">
      <div className="z-10 max-w-5xl w-full items-center justify-between font-mono text-sm lg:flex">
        <h1 className="text-4xl font-bold text-white mb-8 w-full text-center">
          Chess Engine Battle
        </h1>
      </div>

      <div className="relative flex place-items-center w-full justify-center">
        <ChessGame />
      </div>

      <div className="mb-32 grid text-center lg:max-w-5xl lg:w-full lg:mb-0 lg:grid-cols-4 lg:text-left">
        {/* Footer content if needed */}
      </div>
    </main>
  );
}
