import React from 'react';
import {Composition} from 'remotion';
import {Scene3D} from './Scene3D';
export const Root: React.FC = () => (
  <Composition id="Scene3D" component={Scene3D} durationInFrames={90} fps={30} width={1080} height={1920}
    defaultProps={{title: 'TEST'}} />
);
