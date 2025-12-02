#!/usr/bin/perl

$topicName = 'squareCube';
$cmd = 'mv examGenome_flashCard_'.$topicName.'-1.pdf examGenome_flashCard_'.$topicName.'.pdf';
`$cmd`;
for ($i=2; $i <= 11; $i++){
  $oneLess = $i;
  $oneLess--;
  $reName = 'mv examGenome_flashCard_'.$topicName.'-'.$i.'.pdf examGenome_flashCard_'.$topicName.'-'.$oneLess.'.pdf';
  `$reName`;
  print "$reName\n";
}

$zipFile = 'zip -r examGenome_flashCard_'.$topicName.'.zip examGenome_flashCard_'.$topicName.'-*';
`$zipFile`;
sleep(10);
$mvZip = 'mv examGenome_flashCard_'.$topicName.'.zip ../../pdfs/flashcard/';
`$mvZip`;
$mvPdf = 'mv examGenome_flashCard_'.$topicName.'.pdf ../../pdfs/flashcard/';
`$mvPdf`;