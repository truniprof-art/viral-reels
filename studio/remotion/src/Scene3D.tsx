import React from 'react';
import {AbsoluteFill, useCurrentFrame, interpolate, spring, useVideoConfig} from 'remotion';
import {ThreeCanvas} from '@remotion/three';
const Ball: React.FC<{x: number; color: string; delay: number}> = ({x, color, delay}) => {
  const f = useCurrentFrame(); const {fps} = useVideoConfig();
  const s = spring({frame: f - delay, fps, config: {damping: 8}});
  return (<mesh position={[x, -1.2 + s * 1.2, 0]} scale={[1 + 0.25 * (1 - s), 1 - 0.25 * (1 - s), 1]}>
    <sphereGeometry args={[0.8, 48, 48]} /><meshStandardMaterial color={color} roughness={0.35} /></mesh>);
};
export const Scene3D: React.FC<{title: string}> = ({title}) => {
  const f = useCurrentFrame(); const {width, height} = useVideoConfig();
  const op = interpolate(f, [0, 10], [0, 1], {extrapolateRight: 'clamp'});
  return (<AbsoluteFill style={{background: '#10131f'}}>
    <ThreeCanvas width={width} height={height} camera={{position: [0, 0, 7], fov: 50}}>
      <ambientLight intensity={0.6} /><directionalLight position={[3, 5, 5]} intensity={1.6} />
      <Ball x={-1.1} color="#ffb830" delay={0} /><Ball x={1.1} color="#36c2ff" delay={20} />
    </ThreeCanvas>
    <div style={{position: 'absolute', top: 260, width: '100%', textAlign: 'center', color: 'white', fontFamily: 'sans-serif', fontWeight: 900, fontSize: 90, opacity: op}}>{title}</div>
  </AbsoluteFill>);
};
