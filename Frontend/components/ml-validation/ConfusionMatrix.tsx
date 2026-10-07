"use client";

type ConfusionMatrixProps = {
  labels?: string[];
  matrix?: number[][];
};

export function ConfusionMatrix({ labels, matrix }: ConfusionMatrixProps) {
  if (!labels?.length || !matrix?.length) {
    return (
      <p className="text-sm text-white/45">Confusion matrix is not available from the current evaluation.</p>
    );
  }

  const max = Math.max(...matrix.flat(), 1);

  return (
    <div className="overflow-x-auto">
      <table className="min-w-[420px] border-collapse text-xs text-white/75">
        <thead>
          <tr>
            <th className="p-2 text-left text-white/35 font-medium">Actual \\ Predicted</th>
            {labels.map((label) => (
              <th key={label} className="p-2 text-center font-medium text-white/50">
                {label.replace(/_/g, " ")}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {labels.map((rowLabel, ri) => (
            <tr key={rowLabel}>
              <td className="p-2 font-medium text-white/55">{rowLabel.replace(/_/g, " ")}</td>
              {(matrix[ri] || []).map((cell, ci) => {
                const intensity = cell / max;
                return (
                  <td key={`${ri}-${ci}`} className="p-1.5 text-center">
                    <div
                      className="rounded-lg px-2 py-3 font-semibold tabular-nums"
                      style={{
                        background: `rgba(74, 222, 128, ${0.08 + intensity * 0.45})`,
                        color: intensity > 0.55 ? "#ecfdf5" : "rgba(255,255,255,0.75)",
                      }}
                    >
                      {cell}
                    </div>
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
      <p className="mt-3 text-[11px] text-white/35">
        Darker cells indicate more cases. Diagonal cells are correct predictions.
      </p>
    </div>
  );
}
