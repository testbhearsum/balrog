import React, { useState } from 'react';
import { object, arrayOf, node, oneOfType } from 'prop-types';
import classNames from 'classnames';
import { makeStyles } from '@material-ui/styles';
import MuiSpeedDial from '@material-ui/lab/SpeedDial';
import SpeedDialIcon from '@material-ui/lab/SpeedDialIcon';
import CloseIcon from 'mdi-react/CloseIcon';
import DotsVerticalIcon from 'mdi-react/DotsVerticalIcon';

const useStyles = makeStyles(theme => ({
  speedDial: {
    ...theme.mixins.fab,
  },
}));

function SpeedDial({ children, className, ButtonProps, ...props }) {
  const classes = useStyles();
  const [open, setOpen] = useState(false);
  const handleClick = () => setOpen(!open);
  const handleClose = () => setOpen(false);
  const handleOpen = () => setOpen(true);

  return (
    <MuiSpeedDial
      ariaLabel="speed-dial"
      icon={
        <SpeedDialIcon icon={<DotsVerticalIcon />} openIcon={<CloseIcon />} />
      }
      ButtonProps={{ color: 'secondary', ...ButtonProps }}
      className={classNames(classes.speedDial, className)}
      onBlur={handleClose}
      onClick={handleClick}
      onClose={handleClose}
      onFocus={handleOpen}
      onMouseEnter={handleOpen}
      onMouseLeave={handleClose}
      open={open}
      {...props}>
      {children}
    </MuiSpeedDial>
  );
}

SpeedDial.propTypes = {
  /**
   * A set of `SpeedDialAction`s which will be rendered upon interaction
   * with the base `SpeedDial` floating action button.
   */
  children: oneOfType([arrayOf(node), node]).isRequired,
  ButtonProps: object,
};

SpeedDial.defaultProps = {
  ButtonProps: {},
};

export default SpeedDial;
