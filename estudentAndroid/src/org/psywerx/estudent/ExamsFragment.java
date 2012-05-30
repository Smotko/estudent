package org.psywerx.estudent;

import java.util.ArrayList;
import java.util.Iterator;

import org.psywerx.estudent.api.Api;
import org.psywerx.estudent.api.ResponseListener;
import org.psywerx.estudent.extra.D;
import org.psywerx.estudent.extra.HelperFunctions;
import org.psywerx.estudent.json.EnrollmentExamDates;
import org.psywerx.estudent.json.EnrollmentExamDates.EnrollmentExamDate;

import android.app.Activity;
import android.app.ListFragment;
import android.content.Context;
import android.os.Bundle;
import android.view.View;
import android.widget.ListView;

public class ExamsFragment extends ListFragment implements ResponseListener{

	private Context mContext;

	private MenuAdapter mMenuAdapter;
	private OnExamSelectedListener mExamSelectedListener;
	private EnrollmentExamDates mExamDates;
	protected EnrollmentExamDate mExam;
	private String mEnrollmentId;

	protected int mLastPosition = 0;

	public interface OnExamSelectedListener {
		public void onExamSelected(int action);
	}

	@Override
	public void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		mContext = getActivity().getApplicationContext();

		mMenuAdapter = new MenuAdapter(mContext, new ArrayList<MenuItem>());
		setListAdapter(mMenuAdapter);
		D.dbgv("starting exams list");
	}
	
	public void reloadData() {
		if (mExamDates != null){
			mMenuAdapter.clear();
			for(Iterator<EnrollmentExamDate> i = mExamDates.EnrollmentExamDates.iterator(); i.hasNext(); ) {
				EnrollmentExamDate e = i.next();
				mMenuAdapter.add(new MenuItem(
						e.course + " (" + e.exam_key + ")", 
						HelperFunctions.dateToSlo(e.date), 
						e.exam_key, 
						e.signedup ? R.drawable.check_ok_128 : R.drawable.check_no_128));
			}
		}
	}


	@Override
	public void onAttach(Activity activity) {
		super.onAttach(activity);
		mExamSelectedListener = (OnExamSelectedListener) activity;
	}

	@Override
	public void onListItemClick(ListView l, View v, int position, long id) {
		super.onListItemClick(l, v, position, id);

		mLastPosition = position;
		D.dbgv("pos: "+position);
		mExam = mExamDates.EnrollmentExamDates.get(position);
		mExamSelectedListener.onExamSelected(mMenuAdapter.getItem(position).getAction());
	}

	public void onSign(boolean status) {
		if(status)
			mMenuAdapter.getItem(mLastPosition).addIcon(R.drawable.check_ok_128);
		else
			mMenuAdapter.getItem(mLastPosition).addIcon(R.drawable.check_no_128);
		mMenuAdapter.notifyDataSetChanged();
	}

	@Override
	public void onServerResponse(Object response) {
		if (response != null && response instanceof EnrollmentExamDates) {
			mExamDates = (EnrollmentExamDates) response;
			reloadData();
		}
	}

	public void setmEnrollmentId(String mEnrollmentId) {
		this.mEnrollmentId = mEnrollmentId;
		fetchData();
	}

	protected void fetchData() {
		Api.enrollmentExamDatesRequest(this, mEnrollmentId);
	}
}
