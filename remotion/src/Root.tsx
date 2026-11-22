import React from 'react';
import {Composition} from 'remotion';
import {EndCard} from './EndCard';
import {HookImpact} from './HookImpact';
import {ShortThumb} from './ShortThumb';
import {Insight, InsightProps} from './Insight';
import {InsightShort} from './InsightShort';
import {Thumb} from './Thumb';

const empty: InsightProps = {fps: 30, width: 1920, height: 1080, audio: '', duration: 10, scenes: [], post: null, brand: {}};

export const Root: React.FC = () => (
  <>
    <Composition
      id="Insight"
      component={Insight}
      width={1920}
      height={1080}
      fps={30}
      durationInFrames={300}
      defaultProps={empty}
      calculateMetadata={({props}) => ({
        durationInFrames: Math.max(30, Math.round(props.duration * props.fps)),
        fps: props.fps,
        width: props.width,
        height: props.height,
      })}
    />
    <Composition
      id="InsightShort"
      component={InsightShort}
      width={1080}
      height={1920}
      fps={30}
      durationInFrames={300}
      defaultProps={{...empty, width: 1080, height: 1920}}
      calculateMetadata={({props}) => ({
        durationInFrames: Math.max(30, Math.round(props.duration * props.fps)),
        fps: props.fps,
        width: props.width,
        height: props.height,
      })}
    />
    <Composition id="Thumb" component={Thumb} width={1280} height={720} fps={30} durationInFrames={1}
      defaultProps={{text: '', stat: '', brand: 'Smart Penguin Insights'}} />
    <Composition id="HookImpact" component={HookImpact} width={1920} height={1080} fps={30} durationInFrames={270}
      defaultProps={{value: '-$6T', label: 'bốc hơi trong 45 ngày', tag: '45 NGÀY', qAt: 5.9, subAt: 7.4,
        chips: [{text: 'Cổ phiếu Mỹ', s: 2.9}, {text: 'Vàng', s: 3.8}, {text: 'Crypto', s: 4.6}],
        question: 'AI BUBBLE ĐÃ VỠ?', sub: 'Hay cú rũ trước cơ hội lớn?'}} />
    <Composition id="EndCard" component={EndCard} width={1080} height={1920} fps={30} durationInFrames={1}
      defaultProps={{title: "", thumb: null}} />
    <Composition id="ShortThumb" component={ShortThumb} width={1080} height={1920} fps={30} durationInFrames={1}
      defaultProps={{text: '', stat: '', brand: 'Smart Penguin Insights'}} />
  </>
);
