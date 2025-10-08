/* eslint-disable */
import { render, screen } from '@testing-library/react';
import React from 'react';

function Dummy() {
  return <h1>Hello</h1>;
}

test('renders', () => {
  render(<Dummy />);
  expect(screen.getByText('Hello')).toBeInTheDocument();
});
