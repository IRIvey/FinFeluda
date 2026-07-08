import detectiveImg from "../../assets/detective.png";

export function BrandMark({ iconSize = "h-7 w-7", textSize = "text-base", tagline = false }) {
  return (
    <>
      <img src={detectiveImg} alt="" className={`${iconSize} shrink-0`} />
      <span className="flex flex-col leading-none">
        <span className={`font-display font-semibold text-ink ${textSize}`}>FinFeluda</span>
        {tagline && (
          <span className="hidden text-[11px] tracking-wide text-ink-faint sm:block">
            AI Due Diligence Copilot
          </span>
        )}
      </span>
    </>
  );
}
