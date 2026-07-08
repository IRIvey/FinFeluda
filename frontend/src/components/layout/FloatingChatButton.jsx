import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import chatImg from "../../assets/chat.png";

export function FloatingChatButton({ investigationId }) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.7, y: 12 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.5, ease: "easeOut" }}
      className="fixed right-6 bottom-6 z-40"
    >
      {/* Soft pulsing ring to draw the eye without being obnoxious about it. */}
      <motion.span
        aria-hidden="true"
        className="absolute inset-0 rounded-full bg-brand"
        animate={{ opacity: [0.35, 0, 0.35], scale: [1, 1.35, 1] }}
        transition={{ duration: 2.6, repeat: Infinity, ease: "easeInOut" }}
      />
      <Link
        to={`/investigations/${investigationId}/chat`}
        aria-label="Ask AI about this investigation"
        className="group relative flex h-14 w-14 items-center justify-center rounded-full bg-brand shadow-card-hover transition-transform hover:scale-105"
      >
        <img
          src={chatImg}
          alt=""
          className="h-7 w-7"
          style={{ filter: "brightness(0) invert(1)" }}
        />
        <span className="pointer-events-none absolute right-full top-1/2 mr-3 -translate-y-1/2 whitespace-nowrap rounded-md bg-ink px-2.5 py-1.5 text-xs font-medium text-white opacity-0 shadow-card-hover transition-opacity group-hover:opacity-100">
          Ask AI
        </span>
      </Link>
    </motion.div>
  );
}
