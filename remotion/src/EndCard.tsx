import React from 'react';
import {AbsoluteFill, Img, staticFile} from 'remotion';
import {C, FONT, useFonts} from './ui';

// Trọng 22/11: cuối mỗi short có đoạn "xem bản đầy đủ tại..." (thẻ cuối 9:16, nền sạch)
export type EndCardProps = {thumb?: string | null; title: string; channel?: string; accent?: string};
export const EndCard: React.FC<EndCardProps> = ({thumb, title, channel = 'Smart Penguin Insights', accent = '#4F5BD5'}) => {
  useFonts();
  return (
    <AbsoluteFill style={{background: C.bg, fontFamily: FONT, alignItems: 'center'}}>
      <AbsoluteFill style={{background: `radial-gradient(900px 700px at 50% 30%, ${accent}2E, transparent 70%)`}} />
      <div style={{marginTop: 230, display: 'flex', alignItems: 'center', gap: 22}}>
        <Img src={staticFile('logo.png')} style={{width: 110, height: 110, borderRadius: 99, boxShadow: `0 0 0 6px ${accent}33`}} />
        <div style={{fontWeight: 900, fontSize: 40, letterSpacing: 3, color: C.ink}}>{channel.toUpperCase()}</div>
      </div>
      <div style={{marginTop: 70, fontWeight: 900, fontSize: 96, lineHeight: 1.25, color: C.ink, textAlign: 'center', paddingTop: 10}}>XEM BẢN<br />ĐẦY ĐỦ</div>
      <div style={{marginTop: 50, width: 920, borderRadius: 34, overflow: 'hidden', background: '#FFFFFF', border: `1px solid ${C.line}`,
        boxShadow: '0 24px 60px rgba(40,50,110,0.18)', position: 'relative'}}>
        {thumb ? <Img src={staticFile(thumb)} style={{width: 920, height: 518, objectFit: 'cover', display: 'block'}} /> : null}
        <div style={{position: 'absolute', right: 26, top: 518 - 140 - 22, width: 140, height: 140, borderRadius: 99, background: '#FF0033',
          display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 12px 30px rgba(255,0,51,0.35)'}}>
          <div style={{width: 0, height: 0, borderTop: '30px solid transparent', borderBottom: '30px solid transparent', borderLeft: '48px solid #FFFFFF', marginLeft: 10}} />
        </div>
        <div style={{padding: '26px 34px', fontWeight: 800, fontSize: 38, lineHeight: 1.3, color: C.ink}}>{title}</div>
      </div>
      <div style={{marginTop: 50, padding: '18px 40px', borderRadius: 99, background: '#FFFFFF', border: `3px solid ${accent}`,
        fontWeight: 900, fontSize: 44, color: accent}}>▶ YouTube: {channel}</div>
    </AbsoluteFill>
  );
};
